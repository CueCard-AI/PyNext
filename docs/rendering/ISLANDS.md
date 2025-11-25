# PyNext Islands Architecture

> **Selective Hydration for Minimal JavaScript—only ship code for interactive parts.**

---

## Table of Contents

1. [What is Islands Architecture?](#what-is-islands-architecture)
2. [The Mental Model](#the-mental-model)
3. [Overview](#overview)
2. [The Problem with Full Hydration](#the-problem-with-full-hydration)
3. [Islands to the Rescue](#islands-to-the-rescue)
4. [Basic Usage](#basic-usage)
5. [Hydration Strategies](#hydration-strategies)
6. [Static Components](#static-components)
7. [How It Works](#how-it-works)
8. [Bundle Analysis](#bundle-analysis)
9. [Best Practices](#best-practices)
12. [API Reference](#api-reference)

---

## What is Islands Architecture?

### The Aha Moment

> **Islands are the only interactive parts of your page that need JavaScript. Everything else is just HTML—no JS needed.**

Think about this: On a typical blog post, what actually needs to be interactive?
- The header? No, it's just text and links.
- The article content? No, it's just paragraphs and images.
- The sidebar? Usually just links.
- The like button? **YES! That needs to react to clicks.**
- The comment form? **YES! That needs to submit data.**
- The footer? No, just copyright text.

**Islands Architecture says:** Only the like button and comment form need JavaScript. Ship exactly that much—nothing more.

### First Principles: The Ocean & Islands Analogy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE OCEAN & ISLANDS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Imagine your webpage as an OCEAN:                                         │
│                                                                              │
│                                                                              │
│                    ╔══════════════════════════════════════╗                  │
│                    ║         THE OCEAN (Static HTML)      ║                  │
│                    ║                                      ║                  │
│        ░░░░░░░░░░░░║    Everything here is just water    ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║    (static HTML - no JavaScript)    ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║                                      ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║         ┌─────────┐                 ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║         │ 🏝️ Like │ ← ISLAND         ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║         │ Button  │   (interactive!) ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║         └─────────┘                 ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║                                      ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║    ┌──────────┐                     ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║    │ 🏝️ Search │ ← ISLAND            ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║    │ Box      │   (interactive!)    ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║    └──────────┘                     ║░░░░░░░░░░░░      │
│        ░░░░░░░░░░░░║                                      ║░░░░░░░░░░░░      │
│                    ╚══════════════════════════════════════╝                  │
│                                                                              │
│                                                                              │
│   🌊 THE OCEAN = Static HTML (header, article, footer, sidebar...)          │
│      → Ships ZERO JavaScript                                                │
│      → Renders instantly                                                    │
│      → SEO friendly                                                         │
│      → Works without JavaScript                                             │
│                                                                              │
│   🏝️ THE ISLANDS = Interactive components (buttons, forms, counters...)     │
│      → Ships ONLY the JS needed for that component                          │
│      → Hydrated independently                                               │
│      → Can load lazily                                                      │
│      → Tiny bundle sizes                                                    │
│                                                                              │
│                                                                              │
│   RESULT: 95% of your page is static (no JS), 5% is islands (tiny JS)      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Mental Model

### Why Full Hydration is Wasteful

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          THE ELECTRICITY ANALOGY                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   TRADITIONAL APPROACH (Full Hydration):                                    │
│   ──────────────────────────────────────                                    │
│                                                                              │
│   You buy a house and the electrician says:                                 │
│   "I'm going to wire EVERY wall for electricity, even the walls            │
│    that will never have outlets."                                           │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ HOUSE FLOOR PLAN                                                    │   │
│   │                                                                     │   │
│   │  [Bedroom]     [Bathroom]    [Kitchen]                             │   │
│   │  ══════════    ══════════    ══════════  ← ALL walls wired        │   │
│   │   needs 1       needs 1       needs 3       (expensive!)           │   │
│   │   outlet        outlet        outlets                              │   │
│   │                                                                     │   │
│   │  [Closet]      [Hallway]     [Living Room]                         │   │
│   │  ══════════    ══════════    ══════════════                        │   │
│   │   needs 0       needs 0       needs 2                              │   │
│   │   outlets       outlets       outlets                              │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   You wired 18 walls but only need outlets on 7. WASTE!                     │
│                                                                              │
│                                                                              │
│   ISLANDS APPROACH:                                                         │
│   ──────────────────                                                        │
│                                                                              │
│   "Let me only wire the walls where you actually need outlets."             │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ HOUSE FLOOR PLAN                                                    │   │
│   │                                                                     │   │
│   │  [Bedroom]     [Bathroom]    [Kitchen]                             │   │
│   │  ····█····    ····█····    ██████████  ← Only needed walls wired  │   │
│   │   1 outlet     1 outlet     3 outlets      (efficient!)            │   │
│   │                                                                     │   │
│   │  [Closet]      [Hallway]     [Living Room]                         │   │
│   │  ··········    ··········    ····██····                            │   │
│   │   0 outlets    0 outlets     2 outlets                             │   │
│   │                                                                     │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   You only wired 7 walls—the ones that actually need power. EFFICIENT!      │
│                                                                              │
│                                                                              │
│   APPLIED TO JAVASCRIPT:                                                    │
│   ──────────────────────                                                    │
│   • Walls = Page components                                                 │
│   • Electrical wiring = JavaScript                                          │
│   • Outlets = Interactive features                                          │
│                                                                              │
│   Only send JavaScript for components that actually need it!                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Islands Load Independently

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PROGRESSIVE ENHANCEMENT                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ANALOGY: A restaurant kitchen preparing dishes                            │
│                                                                              │
│                                                                              │
│   Traditional (Full Hydration):                                             │
│   ─────────────────────────────                                             │
│                                                                              │
│   "Wait until ALL dishes are ready before serving ANYTHING"                 │
│                                                                              │
│   Appetizer: ready at 2min ─┐                                               │
│   Soup: ready at 5min ──────┼── Wait... wait... wait...                     │
│   Steak: ready at 20min ────┼── NOW serve everything at 20min              │
│   Dessert: ready at 10min ──┘                                               │
│                                                                              │
│   Customer: *hungry for 20 minutes*                                         │
│                                                                              │
│                                                                              │
│   Islands (Independent Hydration):                                          │
│   ─────────────────────────────────                                         │
│                                                                              │
│   "Serve each dish AS SOON AS it's ready"                                   │
│                                                                              │
│   Appetizer: ready at 2min → SERVE! → Customer eating                      │
│   Soup: ready at 5min → SERVE! → Customer eating                           │
│   Dessert: ready at 10min → SERVE! → Customer eating                       │
│   Steak: ready at 20min → SERVE! → Customer eating                         │
│                                                                              │
│   Customer: *eating since minute 2*                                         │
│                                                                              │
│                                                                              │
│   IN PYNEXT:                                                                │
│   ──────────                                                                │
│                                                                              │
│   • Header text: renders immediately (0ms) - static HTML                    │
│   • Article: renders immediately (0ms) - static HTML                        │
│   • Search box: hydrates at 50ms - small island                            │
│   • Comment form: hydrates at 100ms - medium island                        │
│   • Data viz chart: hydrates at 200ms - large island                       │
│                                                                              │
│   User can READ immediately, interact with simple things quickly,           │
│   and complex features activate as they load.                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When to Create an Island

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ISLAND OR NOT?                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ASK: "Does this component need to RESPOND to user interaction?"           │
│                                                                              │
│                                                                              │
│   NEEDS TO BE AN ISLAND (uses JavaScript):                                  │
│   ────────────────────────────────────────                                  │
│   ✓ Click handlers that update UI          → @island                        │
│   ✓ Form inputs that validate/submit       → @island                        │
│   ✓ Counters that increment                → @island                        │
│   ✓ Tabs that switch content               → @island                        │
│   ✓ Dropdowns that open/close              → @island                        │
│   ✓ Infinite scroll loaders                → @island                        │
│   ✓ Real-time data displays                → @island                        │
│                                                                              │
│                                                                              │
│   DOES NOT NEED TO BE AN ISLAND (static HTML):                              │
│   ─────────────────────────────────────────────                             │
│   ✗ Headers with text                      → static                         │
│   ✗ Navigation links (use <a> tags)        → static                         │
│   ✗ Article content                        → static                         │
│   ✗ Images                                 → static                         │
│   ✗ Footer text                            → static                         │
│   ✗ Lists of items (without interaction)   → static                         │
│   ✗ Cards displaying data                  → static                         │
│                                                                              │
│                                                                              │
│   THE RULE OF THUMB:                                                        │
│   ───────────────────                                                       │
│   If clicking/typing/hovering needs to CHANGE something → Island            │
│   If it's just displaying information → Static                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Overview

Islands Architecture is a web architecture pattern that combines:
- **Server-side rendering (SSR)** for fast initial load
- **Selective hydration** for minimal JavaScript
- **Progressive enhancement** for optimal performance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ISLANDS ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          PAGE                                        │    │
│  │                                                                      │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  HEADER (Static)                           0 bytes JS         │  │    │
│  │  │  Logo | Navigation Links | Theme                               │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  SIDEBAR (Static)                          0 bytes JS         │  │    │
│  │  │  Category list, filters                                        │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  MAIN CONTENT (Static)                     0 bytes JS         │  │    │
│  │  │  Article text, images                                          │  │    │
│  │  │                                                                 │  │    │
│  │  │  ┌─────────────────────────────┐  ┌─────────────────────────┐ │  │    │
│  │  │  │  🏝️ COUNTER ISLAND         │  │  🏝️ LIKE BUTTON ISLAND │ │  │    │
│  │  │  │  Interactive!              │  │  Interactive!           │ │  │    │
│  │  │  │  ~500 bytes JS             │  │  ~300 bytes JS          │ │  │    │
│  │  │  └─────────────────────────────┘  └─────────────────────────┘ │  │    │
│  │  │                                                                 │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  │  ┌───────────────────────────────────────────────────────────────┐  │    │
│  │  │  FOOTER (Static)                           0 bytes JS         │  │    │
│  │  │  Links, copyright                                              │  │    │
│  │  └───────────────────────────────────────────────────────────────┘  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  TOTAL JS: 800 bytes  (vs 50KB+ for full hydration)                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Problem with Full Hydration

Traditional SSR frameworks hydrate **the entire page**, even static content:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FULL HYDRATION PROBLEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Page Content                          JavaScript Required                   │
│  ────────────                          ───────────────────                   │
│                                                                              │
│  Header (static text)                  ████ 5KB (React component)            │
│  Navigation (static links)             ████ 3KB (React Router)               │
│  Article (static text)                 ████████████ 15KB (React hydration)   │
│  Sidebar (static list)                 ████ 4KB (React component)            │
│  Counter (actually interactive!)       █ 0.5KB (the only real JS!)          │
│  Footer (static text)                  ███ 3KB (React component)             │
│                                        ────────────────────────              │
│                                        TOTAL: ~30KB JS                       │
│                                                                              │
│  ⚠️ 98% of the JavaScript is for static content!                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Impact on Performance

| Metric | Full Hydration | Islands | Improvement |
|--------|----------------|---------|-------------|
| JavaScript Size | 30-100KB | 0.5-2KB | **95%+ smaller** |
| Parse Time | 50-200ms | 2-10ms | **95%+ faster** |
| Time to Interactive | 500ms+ | 100ms | **5x faster** |
| Main Thread Blocking | High | Minimal | **Smoother** |
| Mobile Performance | Poor | Excellent | ⭐⭐⭐⭐⭐ |

---

## Islands to the Rescue

Islands hydrate **only interactive components**, leaving static content as pure HTML:

```python
from pynext import island, static, page, Signal
from pynext.core.html import div, h1, p, button, footer

@island  # 🏝️ This becomes an interactive island
def Counter():
    count = Signal(0)
    return button(onclick=lambda: count.set(count() + 1))[
        "Count: ", count
    ]

@static  # Explicitly static (optional, default behavior)
def Footer():
    return footer()[
        p()["© 2024 MyApp. All rights reserved."]
    ]

@page
def HomePage():
    return div()[
        h1()["Welcome to My Site"],  # Static - no JS
        p()["This is some content"],  # Static - no JS
        Counter(),                     # 🏝️ Island - gets hydrated
        Footer(),                      # Static - no JS
    ]
```

**Result:**
- Header, content, footer: **0 bytes JS**
- Counter island: **~500 bytes JS**
- Total: **500 bytes** vs 30KB+ for full hydration

---

## Basic Usage

### Creating an Island

```python
from pynext import island, Signal

@island
def InteractiveWidget():
    """This component will be hydrated on the client."""
    value = Signal("")
    
    return div()[
        input_(
            type="text",
            value=value,
            oninput=lambda e: value.set(e.target.value)
        ),
        p()["You typed: ", value],
    ]
```

### Using Islands in Pages

```python
@page
def MyPage():
    return div()[
        h1()["My Page"],           # Static
        p()["Some text content"],  # Static
        InteractiveWidget(),        # 🏝️ Island
        AnotherWidget(),            # 🏝️ Another island
    ]
```

### Islands with Props

```python
@island
def Greeting(name: str = "World", emoji: str = "👋"):
    """Island with props - props are serialized for hydration."""
    return div()[
        span()[f"{emoji} Hello, {name}!"],
        button(onclick=lambda: print(f"Clicked by {name}"))["Wave"],
    ]

# Usage
Greeting(name="Alice", emoji="🎉")
```

---

## Hydration Strategies

PyNext supports multiple hydration strategies to optimize when JavaScript loads:

### 1. Load (Default)

Hydrate immediately when the page loads.

```python
@island  # or @island(strategy=HydrationStrategy.LOAD)
def CriticalWidget():
    """Hydrates immediately - for above-the-fold interactive content."""
    return button(onclick=handle_click)["Click Me"]
```

**Use for:** Above-the-fold interactive elements, critical functionality.

### 2. Visible

Hydrate when the island scrolls into view.

```python
@island(strategy=HydrationStrategy.VISIBLE)
def LazyChart():
    """Hydrates when scrolled into view - saves initial load time."""
    return div()[Chart(data=chart_data)]
```

**Use for:** Below-the-fold content, charts, comments sections.

### 3. Idle

Hydrate when the browser is idle or on user interaction.

```python
@island(strategy=HydrationStrategy.IDLE)
def LowPriorityWidget():
    """Hydrates on idle or first interaction - minimal impact."""
    return div()[
        button(onclick=handle_click)["Do Something"],
    ]
```

**Use for:** Nice-to-have interactions, secondary features.

### 4. Media

Hydrate only when a media query matches.

```python
@island(strategy=HydrationStrategy.MEDIA, media="(min-width: 768px)")
def DesktopOnlyWidget():
    """Only hydrates on desktop - saves mobile bandwidth."""
    return div()[ComplexDesktopUI()]
```

**Use for:** Desktop-only features, responsive enhancements.

### 5. None

Never hydrate - SSR only.

```python
@island(strategy=HydrationStrategy.NONE)
def ServerOnlyWidget():
    """Renders on server, never hydrated - for dynamic but non-interactive content."""
    return div()[
        p()[f"Server time: {datetime.now()}"],
    ]
```

**Use for:** Dynamic content that doesn't need client interactivity.

---

## Strategy Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HYDRATION STRATEGY TIMELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PAGE LOAD                                                                   │
│  │                                                                           │
│  │  LOAD Strategy: ████████████████████████████████████████████ Immediate   │
│  │                 ↑ Hydrates now                                            │
│  │                                                                           │
│  │  IDLE Strategy: ─────────────────────────█████████████████── When idle   │
│  │                                          ↑ Browser idle                   │
│  │                                                                           │
│  │                           USER SCROLLS                                    │
│  │                           │                                               │
│  │  VISIBLE Strategy: ───────┴───────────────█████████████████ When visible │
│  │                                           ↑ Enters viewport               │
│  │                                                                           │
│  │                                      VIEWPORT RESIZES                     │
│  │                                      │                                    │
│  │  MEDIA Strategy: ────────────────────┴────█████████████████ When matches │
│  │                                           ↑ min-width: 768px              │
│  │                                                                           │
│  │  NONE Strategy: ───────────────────────────────────────────── Never      │
│  │                                                                           │
│  ▼                                                                           │
│  TIME                                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Static Components

For components that should never be hydrated, use `@static`:

```python
from pynext import static

@static
def Footer():
    """Explicitly static - guaranteed no JavaScript."""
    return footer()[
        nav()[
            a(href="/about")["About"],
            a(href="/contact")["Contact"],
        ],
        p()["© 2024 Company"],
    ]
```

### When to Use @static

- **Always:** For truly static content (headers, footers, navigation)
- **Optional:** Most components are static by default
- **Explicit:** When you want to document intent

### Default Behavior

Components without decorators are treated as static unless they:
- Contain signals, stores, or effects
- Have event handlers (onclick, oninput, etc.)
- Contain island children

```python
# These are all static by default (no @static needed):

def Header():
    return header()[h1()["My Site"]]

def ArticleContent():
    return article()[p()["Content..."]]

def StaticList():
    return ul()[[li()[item] for item in items]]
```

---

## How It Works

### Server-Side Rendering

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SERVER-SIDE RENDERING                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Python renders entire page                                              │
│     ┌────────────────────────────────────────────────────────────────────┐  │
│     │ @page                                                               │  │
│     │ def HomePage():                                                     │  │
│     │     return div()[                                                   │  │
│     │         Header(),          ← Renders to HTML                        │  │
│     │         Counter(),         ← Island: renders + adds markers         │  │
│     │         Footer(),          ← Renders to HTML                        │  │
│     │     ]                                                               │  │
│     └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  2. Islands get special attributes                                          │
│     ┌────────────────────────────────────────────────────────────────────┐  │
│     │ <div data-island="island-Counter-abc123"                           │  │
│     │      data-hydrate="load"                                           │  │
│     │      data-component="Counter">                                     │  │
│     │   <button>Count: 0</button>                                        │  │
│     │ </div>                                                              │  │
│     └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  3. Hydration data embedded in page                                         │
│     ┌────────────────────────────────────────────────────────────────────┐  │
│     │ <script>                                                            │  │
│     │   __pynext__.registerIsland("island-Counter-abc123", {             │  │
│     │     component: "Counter",                                           │  │
│     │     strategy: "load",                                               │  │
│     │     props: {},                                                      │  │
│     │     signals: ["signal-count-xyz"]                                   │  │
│     │   });                                                               │  │
│     │   __pynext__.hydrateIslands();                                     │  │
│     │ </script>                                                           │  │
│     └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Client-Side Hydration

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLIENT-SIDE HYDRATION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Page loads with server-rendered HTML                                    │
│     └─> User sees content immediately!                                      │
│                                                                              │
│  2. islands.js runtime executes                                             │
│     └─> Reads registered islands                                            │
│     └─> Applies hydration strategies                                        │
│                                                                              │
│  3. For each island (based on strategy):                                    │
│     ┌────────────────────────────────────────────────────────────────────┐  │
│     │ LOAD:    Hydrate immediately                                        │  │
│     │ VISIBLE: Set up IntersectionObserver, hydrate when visible          │  │
│     │ IDLE:    Use requestIdleCallback, or hydrate on interaction         │  │
│     │ MEDIA:   Set up matchMedia listener, hydrate when matches           │  │
│     │ NONE:    Skip hydration                                             │  │
│     └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  4. Hydration process for each island:                                      │
│     a) Find island element by data-island attribute                         │
│     b) Connect event handlers                                               │
│     c) Initialize signals with server state                                 │
│     d) Set up reactivity                                                    │
│     e) Mark as hydrated                                                     │
│                                                                              │
│  5. Island becomes interactive                                              │
│     └─> Events work                                                         │
│     └─> Signals update DOM                                                  │
│     └─> data-hydrated="true" added                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Bundle Analysis

### What Gets Bundled

| Component Type | JavaScript Bundle | Size |
|----------------|-------------------|------|
| Static component | None | 0 bytes |
| Signal-only island | signals.js | ~1KB |
| Event-only island | events.js | ~0.5KB |
| Full island | signals + events | ~1.5KB |
| With Resource | + resource.js | ~0.5KB |
| With Store | + store.js | ~0.3KB |

### Bundle Requirements Detection

PyNext automatically detects what each island needs:

```python
@island
def Counter():
    count = Signal(0)  # Needs: signals
    return button(onclick=lambda: count.set(count() + 1))[count]  # Needs: events

# Bundle includes: signals.js, events.js (~1.5KB)
```

```python
@island
def DataWidget():
    data = Resource(fetch_data)  # Needs: resource, signals
    return div()[data()]

# Bundle includes: signals.js, resource.js (~1.5KB)
```

### Minimal Runtime Selection

```python
from pynext.core.island import get_minimal_runtime_for_island

# Analyze what an island needs
modules = get_minimal_runtime_for_island(counter_island)
# Returns: ["core", "signals"]

# Only those modules are included in the bundle
```

---

## Best Practices

### 1. Island Granularity

```python
# ❌ Bad: Large island with mostly static content
@island
def ProductPage():
    return div()[
        h1()["Product Name"],           # Static
        p()["Description..."],           # Static
        img(src="product.jpg"),          # Static
        p()["More static content..."],   # Static
        AddToCartButton(),               # Interactive
    ]

# ✓ Good: Small, focused island
def ProductPage():
    return div()[
        h1()["Product Name"],           # Static
        p()["Description..."],           # Static
        img(src="product.jpg"),          # Static
        p()["More static content..."],   # Static
        AddToCartIsland(),               # Only this is an island
    ]

@island
def AddToCartIsland():
    return AddToCartButton()
```

### 2. Strategy Selection

```python
# ✓ Good: Match strategy to use case

# Critical interactive element - load immediately
@island(strategy=HydrationStrategy.LOAD)
def NavigationMenu():
    ...

# Below-the-fold content - hydrate when visible
@island(strategy=HydrationStrategy.VISIBLE)
def CommentsSection():
    ...

# Nice-to-have feature - hydrate when idle
@island(strategy=HydrationStrategy.IDLE)
def ShareButtons():
    ...

# Desktop-only feature
@island(strategy=HydrationStrategy.MEDIA, media="(min-width: 1024px)")
def AdvancedFilters():
    ...
```

### 3. Avoid Island Nesting

```python
# ❌ Bad: Nested islands (unnecessary overhead)
@island
def OuterIsland():
    return div()[
        InnerIsland(),  # Another island inside!
    ]

# ✓ Good: Flat island structure
def Container():
    return div()[
        FirstIsland(),
        SecondIsland(),
    ]
```

### 4. Use Static for Clarity

```python
# ✓ Good: Document intent with @static
@static
def PageHeader():
    """This will never need JavaScript."""
    return header()[...]

@static
def PageFooter():
    """This will never need JavaScript."""
    return footer()[...]
```

---

## API Reference

### @island Decorator

```python
@island
@island(strategy=HydrationStrategy.LOAD)
@island(strategy=HydrationStrategy.VISIBLE)
@island(strategy=HydrationStrategy.IDLE)
@island(strategy=HydrationStrategy.MEDIA, media="(min-width: 768px)")
@island(strategy=HydrationStrategy.NONE)
```

**Parameters:**
- `strategy`: When to hydrate (default: `LOAD`)
- `media`: Media query string for `MEDIA` strategy

### @static Decorator

```python
@static
def Component():
    ...
```

Explicitly marks a component as static (no hydration).

### HydrationStrategy Enum

```python
from pynext import HydrationStrategy

HydrationStrategy.LOAD     # Hydrate immediately
HydrationStrategy.VISIBLE  # Hydrate when in viewport
HydrationStrategy.IDLE     # Hydrate when browser idle
HydrationStrategy.MEDIA    # Hydrate when media query matches
HydrationStrategy.NONE     # Never hydrate
```

### Utility Functions

```python
from pynext import is_interactive, collect_islands, get_island_hydration_data

# Check if component needs hydration
is_interactive(component)  # -> bool

# Collect all islands from a component tree
collect_islands(page_component)  # -> List[IslandBoundary]

# Generate hydration data for islands
get_island_hydration_data(islands)  # -> Dict
```

---

## Related Documentation

- [Streaming & Suspense](./STREAMING_SUSPENSE.md) - Progressive rendering
- [Hydration](./HYDRATION.md) - Server-to-client state transfer
- [State Management](./STATE_MANAGEMENT.md) - Signals and reactivity

---

## Demo

```bash
# Run island tests
python -m pytest tests/unit/test_islands.py -v
```

