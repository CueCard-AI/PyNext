# Configuration Guide

Every PyNext application can be customized through configuration. This guide walks you through each configuration option, explaining not just *what* each setting does, but *why* you'd want to change it and *when* to use different values.

**What you'll learn:**
- How to set up Python and JavaScript dependencies
- Configuring your development server
- Preparing your app for production
- Managing secrets with environment variables
- Advanced customization options

---

## Table of Contents

- [Configuration File](#configuration-file) — Where configuration lives
- [Dependency Files](#dependency-files) — Managing Python and npm packages
- [Server Settings](#server-settings) — Host, port, workers, timeouts
- [NPM Packages (Legacy)](#npm-packages-legacy-configuration) — Advanced bundler options
- [Static Files](#static-files) — Serving images, CSS, fonts
- [Build Options](#build-options) — Minification, source maps, optimization
- [Development Settings](#development-settings) — Hot reload, logging, errors
- [Production Settings](#production-settings) — Security, performance, deployment
- [Environment Variables](#environment-variables) — Managing secrets safely
- [Advanced Configuration](#advanced-configuration) — Middleware, plugins, databases
- [Complete Reference](#complete-reference) — All options at a glance

---

## Configuration File

### What is `pynext.config.py`?

Every PyNext project has a configuration file called `pynext.config.py`. It's a regular Python file where you define settings for your application — things like what port to run on, how to handle static files, and what npm packages to bundle.

**Why a Python file?** Unlike JSON or YAML configuration, a Python file lets you:
- Use environment variables (`os.getenv()`)
- Add conditional logic (`if IS_PROD: ...`)
- Import from other files
- Add comments explaining your choices

### Where to Put It

The config file lives in your project's root directory, alongside your `pages/` folder:

```
my-app/
├── pages/                    ← Your page components
│   └── index.py
├── components/               ← Reusable components
├── public/                   ← Static files (images, CSS)
├── pynext.config.py         ← Configuration file (this is what we're discussing!)
├── pynext.requirements.txt  ← Python dependencies
└── pynext.npm.txt           ← JavaScript dependencies
```

### A Minimal Configuration

You don't need to configure everything — PyNext has sensible defaults. Here's a minimal config that just sets the basics:

```python
# pynext.config.py

# Development server settings
host = "localhost"    # Only accessible from your machine
port = 3000           # http://localhost:3000
debug = True          # Show helpful error messages
```

That's it! With just 3 lines, you have a working development server.

### A More Complete Example

As your app grows, you'll add more configuration:

```python
# pynext.config.py

import os

# Detect if we're in production
IS_PROD = os.getenv("PYNEXT_ENV") == "production"

# Server settings
host = "0.0.0.0" if IS_PROD else "localhost"
port = int(os.getenv("PORT", 3000))
debug = not IS_PROD

# Security
secret_key = os.getenv("SECRET_KEY", "dev-only-secret")

# Static files
static_dir = "public"
static_cache_max_age = 31536000 if IS_PROD else 0  # 1 year in prod
```

### Quick Reference: All Configuration Categories

| Category | What it controls | Key options |
|----------|------------------|-------------|
| **Server** | How the app runs | `host`, `port`, `debug`, `workers` |
| **Dependencies** | External packages | `pynext.requirements.txt`, `pynext.npm.txt` |
| **Static Files** | Images, CSS, fonts | `static_dir`, `static_url`, `static_cache_max_age` |
| **Build** | Production optimization | `minify`, `source_maps`, `code_splitting` |
| **Development** | Dev experience | `hot_reload`, `log_level`, `show_error_details` |
| **Security** | Production safety | `secret_key`, `cors_origins`, `csrf_enabled` |

Now let's explore each category in detail.

---

## Dependency Files

When building a PyNext application, you'll likely need external packages — Python libraries for your server-side logic (like pandas for data analysis or sqlalchemy for database access), and JavaScript packages for client-side features (like chart.js for visualizations).

PyNext uses two simple text files to manage these dependencies. If you've ever used a `requirements.txt` file in Python, you already know the format. We use the same familiar pattern for both Python and JavaScript packages.

### Why Two Separate Files?

Think of your PyNext app as having two environments:

1. **The Server** (Python) — Where your Server Actions run. This is where you process data, query databases, run ML models, etc.

2. **The Browser** (JavaScript) — Where your interactive UI lives. This is where charts render, animations play, and users interact with components.

Each environment needs its own dependencies, so we keep them separate:

```
my-app/
├── pages/
├── components/
├── public/
├── pynext.config.py          ← App settings (port, build options, etc.)
├── pynext.requirements.txt   ← Python packages for the SERVER
└── pynext.npm.txt            ← JavaScript packages for the BROWSER
```

---

### Step 1: Setting Up Python Dependencies

**When do you need this?** Whenever you want to use a Python package inside a Server Action. For example, if you want to analyze data with pandas, query a database with SQLAlchemy, or call an AI model with transformers.

**How to set it up:**

Create a file called `pynext.requirements.txt` in your project root. This file uses the exact same format as a standard Python requirements file — one package per line, with optional version specifiers.

```txt
# pynext.requirements.txt
#
# List the Python packages your Server Actions need.
# This uses standard pip format — if you've used requirements.txt before,
# you already know how this works!

# Data Processing
# We're using pandas for analyzing CSV files and numpy for calculations
pandas>=2.0.0
numpy>=1.24.0

# Database Access  
# SQLAlchemy lets us query databases, asyncpg is for PostgreSQL
sqlalchemy>=2.0.0
asyncpg>=0.28.0

# HTTP Requests
# For calling external APIs from our server actions
httpx>=0.25.0
```

**Understanding version specifiers:**

| Format | Meaning | Example |
|--------|---------|---------|
| `package` | Latest version | `pandas` |
| `package>=1.0.0` | Version 1.0.0 or higher | `pandas>=2.0.0` |
| `package==1.0.0` | Exactly version 1.0.0 | `pandas==2.0.0` |
| `package>=1.0,<2.0` | Between 1.0 and 2.0 | `pandas>=1.0,<2.0` |

**Now you can use these packages in your Server Actions:**

Once a package is listed in `pynext.requirements.txt`, you can import and use it in any Server Action:

```python
from pynext import server_action

@server_action
async def analyze_sales(file_path: str):
    # pandas is available because we listed it in pynext.requirements.txt!
    import pandas as pd
    
    # Read the CSV file and calculate some statistics
    df = pd.read_csv(file_path)
    
    return {
        "total_sales": df["amount"].sum(),
        "average_sale": df["amount"].mean(),
        "top_product": df.groupby("product")["amount"].sum().idxmax()
    }
```

The key insight here is that Server Actions run on your Python server, so they have access to the entire Python ecosystem — pandas, numpy, scikit-learn, transformers, whatever you need.

---

### Step 2: Setting Up JavaScript Dependencies

**When do you need this?** Whenever you want to use a JavaScript library in the browser. For example, if you want to render charts with Chart.js, add animations with Framer Motion, or use a UI component library like Material-UI.

**How to set it up:**

Create a file called `pynext.npm.txt` in your project root. This file lists npm packages, one per line, with an optional version after `@`.

```txt
# pynext.npm.txt
#
# List the npm packages your browser-side code needs.
# Format: package-name@version (version is optional)

# Charts
# Chart.js is great for simple charts, D3 for complex visualizations
chart.js@^4.4.0
d3@^7.0.0

# Utilities
# Lodash has helpful functions, date-fns handles dates nicely
lodash@^4.17.0
date-fns@^3.0.0
```

**Understanding npm versions:**

| Format | Meaning | Example |
|--------|---------|---------|
| `package` | Latest version | `lodash` |
| `package@^4.0.0` | Compatible with 4.x.x | `lodash@^4.17.0` |
| `package@~4.17.0` | Approximately 4.17.x | `lodash@~4.17.0` |
| `package@4.17.21` | Exactly this version | `lodash@4.17.21` |

**What about scoped packages?**

Some npm packages are "scoped" — they have an organization prefix like `@mui/` or `@emotion/`. These work the same way, just include the full name:

```txt
# Scoped packages have an @ at the start of their name
# The version @ comes after the package name

@mui/material@^5.14.0
@emotion/react@^11.0.0
@radix-ui/react-dialog@^1.0.0
```

**Using npm packages in your components:**

Once a package is listed, you can import and use it in your PyNext components:

```python
from pynext import component, div, canvas
from pynext.bundler import npm_import

@component
def SalesChart(data: list):
    # npm_import returns the URL to the bundled package
    chart_url = npm_import("chart.js")
    
    return div()[
        canvas(id="myChart"),
        script(type="module")[f'''
            import {{ Chart }} from "{chart_url}";
            
            new Chart(document.getElementById("myChart"), {{
                type: "bar",
                data: {data}
            }});
        ''']
    ]
```

---

### Step 3: Installing Your Dependencies

Now that you've defined what packages you need, let's install them. PyNext provides a simple CLI command that handles both Python and npm packages at once.

**The quick way — install everything:**

```bash
pynext deps install
```

This single command:
1. Reads your `pynext.requirements.txt` and runs `pip install`
2. Reads your `pynext.npm.txt`, creates a `package.json`, and runs `npm install`

You'll see output like:

```
[PyNext] Installing dependencies...
[PyNext] Python dependencies installed ✓
[PyNext] NPM dependencies installed ✓
```

**Installing just one type:**

Sometimes you only want to install one type of dependency:

```bash
# Only install Python packages
pynext deps install --python

# Only install npm packages  
pynext deps install --npm
```

**Checking what's missing:**

Not sure if your dependencies are installed? Use the check command:

```bash
pynext deps check
```

This scans your dependency files and tells you what's missing:

```
[PyNext] Checking dependencies...
[PyNext] Missing Python packages: pandas, numpy
[PyNext] Missing NPM packages: chart.js
[PyNext] Run 'pynext deps install' to install missing dependencies
```

---

### Step 4: The Development Server Handles It Automatically

Here's the really convenient part — when you run `pynext dev`, PyNext automatically checks your dependencies and offers to install anything that's missing:

```bash
$ pynext dev
[PyNext] Checking dependencies...
[PyNext] Missing Python packages: pandas, numpy
[PyNext] Missing NPM packages: chart.js
[PyNext] Installing missing dependencies...
[PyNext] Python dependencies installed ✓
[PyNext] NPM dependencies installed ✓
[PyNext] Starting development server on http://localhost:3000
```

This means you can add a new package to your dependency file, restart the dev server, and it will be automatically installed. No need to remember to run a separate install command!

**If you want to skip this automatic behavior:**

```bash
# Skip the dependency check entirely (faster startup)
pynext dev --skip-deps

# Check but don't auto-install (just warn about missing packages)
pynext dev --no-install
```

---

### Step 5: Creating New Dependency Files

Starting a new project and need to create these files from scratch? PyNext can generate templates for you:

```bash
pynext deps init
```

This creates both `pynext.requirements.txt` and `pynext.npm.txt` with helpful comments and examples. You can then edit them to add the packages you actually need.

If you used `pynext init my-project` to create your project, these files are already created for you.

---

### Special Case: React Component Libraries

Many npm packages are built for React — UI libraries like Material-UI, animation libraries like Framer Motion, etc. Normally, using these would require shipping the entire React library (about 40KB).

PyNext is smart about this. When it detects React-based packages in your `pynext.npm.txt`, it automatically uses **Preact** instead — a tiny 4KB library that's compatible with most React code.

**You don't need to do anything special.** Just add React-based packages to your npm file:

```txt
# pynext.npm.txt

# These are React component libraries
# PyNext automatically uses Preact (~4KB) instead of React (~40KB)
@mui/material@^5.14.0
framer-motion@^10.0.0
@headlessui/react@^1.7.0
```

PyNext detects package names that contain `react`, `@mui/`, `@radix-ui/`, `@chakra-ui/`, `@emotion/react`, `framer-motion`, and similar patterns, and enables Preact compatibility automatically.

---

### Summary: The Complete Workflow

Let's recap the complete workflow for managing dependencies:

1. **Add Python packages** to `pynext.requirements.txt`:
   ```txt
   pandas>=2.0.0
   sqlalchemy>=2.0.0
   ```

2. **Add npm packages** to `pynext.npm.txt`:
   ```txt
   chart.js@^4.4.0
   lodash@^4.17.0
   ```

3. **Install everything** with one command:
   ```bash
   pynext deps install
   ```

4. **Or just start the dev server** and let it auto-install:
   ```bash
   pynext dev
   ```

5. **Use your packages:**
   - Python packages → available in `@server_action` functions
   - npm packages → available via `npm_import()` in components

---

### Migrating from the Old Format

If you were using the older `npm_packages` list in `pynext.config.py`, migration is simple:

**Before (in pynext.config.py):**
```python
npm_packages = [
    "chart.js",
    {"lodash": "^4.17.0"},
]
```

**After (in pynext.npm.txt):**
```txt
chart.js
lodash@^4.17.0
```

The old format still works for backward compatibility, so your existing projects won't break. But we recommend migrating to the new format because:

- It's simpler (no Python syntax, just a text list)
- It's separate from configuration (cleaner project structure)
- It's consistent with how Python dependencies work (`requirements.txt` style)

---

## Server Settings

The server settings control how PyNext runs your application — what port it listens on, how many requests it can handle, and how it behaves in development vs production.

### Understanding Host and Port

**What is "host"?** The host setting determines which network interfaces your server listens on. Think of it like deciding which doors of your house are open to visitors.

**What is "port"?** The port is like an apartment number — it's how computers know which application to send requests to. Web browsers default to port 80 (HTTP) or 443 (HTTPS), but during development we typically use port 3000.

**The common scenarios:**

| Scenario | Host | Port | URL |
|----------|------|------|-----|
| Local development | `localhost` | `3000` | http://localhost:3000 |
| Docker container | `0.0.0.0` | `3000` | http://container-ip:3000 |
| Production (behind nginx) | `127.0.0.1` | `8000` | (nginx handles public access) |

**Setting it up:**

```python
# pynext.config.py

# For local development (only your computer can access it)
host = "localhost"
port = 3000

# To allow access from other devices on your network
# (useful for testing on phones, or in Docker)
host = "0.0.0.0"

# Use a different port if 3000 is taken
port = 8080
```

**Pro tip:** During development, `localhost` is safer because it prevents other devices on your network from accessing your development server. Switch to `0.0.0.0` only when you need external access.

---

### Debug Mode: Development vs Production

**What does debug mode do?** When debug mode is on, PyNext runs in a developer-friendly way: it shows detailed error messages, automatically reloads when you change files, and provides extra logging to help you understand what's happening.

**Why turn it off in production?** Detailed error pages can reveal sensitive information about your code. Auto-reload wastes resources. You want production to be fast and secure, not developer-friendly.

| Feature | Debug ON | Debug OFF |
|---------|----------|-----------|
| Error pages | Show full stack traces | Show generic "500 Error" page |
| File watching | Auto-reload on changes | No watching (faster) |
| Logging | Verbose (every request) | Minimal (errors only) |
| API docs | Available at `/_pynext/docs` | Disabled |

**Setting it up:**

```python
# pynext.config.py

# During development (the default)
debug = True

# In production (you should set this!)
debug = False
```

**How do you switch between them?** The best practice is to use environment variables so you don't have to change the config file:

```python
# pynext.config.py
import os

# Automatically detect based on environment
debug = os.getenv("PYNEXT_ENV") != "production"
```

---

### Workers: Handling Multiple Requests

**What are workers?** When a single Python process handles requests one at a time, it can only serve one user at a time. Workers are additional processes that run in parallel, allowing your server to handle many requests simultaneously.

**The analogy:** Think of a coffee shop. With one barista (1 worker), customers wait in line. With four baristas (4 workers), four customers can be served at once.

**How many workers should you use?** A common formula is:

```
workers = (number of CPU cores × 2) + 1
```

So a 4-core machine would have 9 workers. This accounts for the fact that some workers may be waiting for I/O (database, external APIs) while others are doing CPU work.

**Setting it up:**

```python
# pynext.config.py
import os

# Fixed number of workers
workers = 4

# Or calculate based on your server's CPU
workers = (os.cpu_count() or 1) * 2 + 1
```

**Important:** Workers are for production only. During development, you only need one worker (and that's the default). Multiple workers would interfere with hot reload.

---

### Timeouts: Preventing Stuck Requests

**Why do we need timeouts?** Sometimes things go wrong — a database query takes forever, an external API doesn't respond, or there's a bug causing an infinite loop. Timeouts prevent these situations from tying up your server indefinitely.

**The three timeout types:**

| Timeout | What it does | Default | When to change |
|---------|--------------|---------|----------------|
| `request_timeout` | Max time for a single request | 30s | If you have long-running operations |
| `keep_alive` | How long to keep connections open | 5s | Usually leave as default |
| `shutdown_timeout` | Time to finish requests during shutdown | 30s | If your requests take longer |

**Setting it up:**

```python
# pynext.config.py

# If your Server Actions might take a while (e.g., ML inference)
request_timeout = 60  # 60 seconds instead of 30

# How long to wait for a client to send another request
# on the same connection (keep-alive)
keep_alive = 5

# When you stop the server, how long to wait for
# in-progress requests to finish
shutdown_timeout = 30
```

**Pro tip:** If users are seeing timeout errors, first check if your Server Actions are actually slow (add logging!), rather than just increasing the timeout.

---

## NPM Packages (Legacy Configuration)

> **Note:** The recommended way to manage npm packages is now through `pynext.npm.txt` (see [Dependency Files](#dependency-files) above). This section documents the older `pynext.config.py` approach, which still works for backward compatibility.

**When to use this approach:** If you need advanced bundler options (like custom esbuild settings or package aliases) that aren't available in the simple `pynext.npm.txt` format.

---

### The Basics: Adding npm Packages via Config

If you prefer to keep everything in one Python file, you can list npm packages directly in your config:

```python
# pynext.config.py

npm_packages = [
    "chart.js",    # Gets the latest version
    "lodash",
    "dayjs"
]
```

PyNext will install these packages and bundle them so they're available in your browser-side code.

---

### Version Pinning: Controlling Which Version You Get

**Why pin versions?** Without version pinning, you get "latest" — which might change tomorrow and break your app. Pinning ensures reproducible builds.

**The syntax:** You can use npm's semver (semantic versioning) syntax:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `"package"` | Latest version (risky!) | `"lodash"` |
| `{"package": "4.17.21"}` | Exact version | `{"lodash": "4.17.21"}` |
| `{"package": "^4.17.0"}` | Compatible (4.x.x) | `{"lodash": "^4.17.0"}` |
| `{"package": "~4.17.0"}` | Approximately (4.17.x) | `{"lodash": "~4.17.0"}` |

```python
# pynext.config.py

npm_packages = [
    "chart.js",                       # Latest (convenient but risky)
    {"lodash": "^4.17.0"},            # Any 4.x version (safe minor updates)
    {"dayjs": "1.11.10"},             # Exact version (most predictable)
    {"axios": ">=1.0.0 <2.0.0"}       # Between 1.0 and 2.0
]
```

**Pro tip:** Start with `^` (caret) for most packages — it allows bug fixes but prevents breaking changes.

---

### React Compatibility: Using React Libraries with Preact

**The problem:** Many great UI libraries (Material-UI, Framer Motion, etc.) are built for React, which is about 40KB. That's a lot of JavaScript just to use a button component.

**The solution:** PyNext can swap React for Preact — a tiny 4KB library that's API-compatible with React. Most React libraries work perfectly with Preact.

**How to enable it:**

```python
# pynext.config.py

# Tell PyNext to use Preact instead of React
react_compat = True

# Now you can use React-based packages
npm_packages = [
    "@mui/material",      # Material-UI components
    "react-query",        # Data fetching
    "recharts"            # Charts
]
```

**What happens behind the scenes:**
- `import React from 'react'` → uses Preact
- `import ReactDOM from 'react-dom'` → uses Preact
- JSX works as expected

**Note:** If you use `pynext.npm.txt`, React compatibility is auto-detected from package names — you don't need to set `react_compat` manually.

---

### Advanced: Customizing the Bundler

PyNext uses [esbuild](https://esbuild.github.io/) under the hood — one of the fastest JavaScript bundlers available. You can customize its behavior:

```python
# pynext.config.py

# Where bundled files are stored
bundle_dir = ".pynext/bundles"

# Fine-tune esbuild behavior
esbuild_options = {
    "target": "es2020",       # JavaScript version (es2015, es2020, etc.)
    "format": "esm",          # Output format (esm = ES modules)
    "minify": True,           # Shrink the code
    "sourcemap": True,        # Generate source maps for debugging
    "splitting": True,        # Split into smaller chunks
    "tree_shaking": True,     # Remove unused code
}
```

**When to change these:**
- **target**: Lower it (e.g., `es2015`) if you need to support older browsers
- **minify**: Turn off during debugging to read the generated code
- **sourcemap**: Turn off in production if you don't want to expose source code

---

### Custom Aliases: Shortening Import Paths

If you're used to React projects with path aliases like `@/components`, you can set those up:

```python
# pynext.config.py

package_aliases = {
    # Make React → Preact swap explicit
    "react": "preact/compat",
    "react-dom": "preact/compat",
    
    # Custom path aliases
    "@/": "./src/",           # @/utils → ./src/utils
    "@components/": "./components/"
}
```

This is an advanced feature — most PyNext apps don't need custom aliases.

---

## Static Files

Static files are assets that don't change — images, CSS stylesheets, fonts, downloadable PDFs, etc. Unlike your Python pages (which are generated dynamically), static files are served directly to the browser as-is.

### Understanding the Setup

**The default structure:** PyNext looks for static files in a folder called `public/` (or `static/`) at your project root:

```
my-app/
├── pages/
│   └── index.py
├── public/                    ← Static files go here
│   ├── styles.css
│   ├── logo.png
│   └── downloads/
│       └── brochure.pdf
└── pynext.config.py
```

**How URLs map to files:**

| File Path | URL |
|-----------|-----|
| `public/styles.css` | `/styles.css` |
| `public/logo.png` | `/logo.png` |
| `public/downloads/brochure.pdf` | `/downloads/brochure.pdf` |

**Using static files in your pages:**

```python
from pynext import page, div, img, link

@page
def home():
    return div()[
        # Reference the CSS file
        link(rel="stylesheet", href="/styles.css"),
        
        # Reference an image
        img(src="/logo.png", alt="Logo"),
        
        # Link to a download
        a(href="/downloads/brochure.pdf")["Download Brochure"]
    ]
```

---

### Customizing the Static File Location

If you prefer a different folder name or URL prefix, you can change them:

```python
# pynext.config.py

# The folder where static files live
static_dir = "assets"          # Instead of "public"

# The URL prefix for accessing them
static_url = "/static"         # Now: /static/logo.png instead of /logo.png
```

**After this change:**

| File Path | URL |
|-----------|-----|
| `assets/styles.css` | `/static/styles.css` |
| `assets/logo.png` | `/static/logo.png` |

---

### Multiple Static Directories

Sometimes you need files served from different folders — maybe user uploads go in one place and app assets in another:

```python
# pynext.config.py

static_dirs = [
    {"path": "public", "url": "/"},           # App assets at root
    {"path": "uploads", "url": "/uploads"},    # User uploads
    {"path": "docs", "url": "/docs"}           # Documentation files
]
```

**Example:**

| File Path | URL |
|-----------|-----|
| `public/logo.png` | `/logo.png` |
| `uploads/avatar-123.jpg` | `/uploads/avatar-123.jpg` |
| `docs/api-reference.pdf` | `/docs/api-reference.pdf` |

---

### Caching: Making Your Site Faster

**The problem:** Every time someone visits your site, their browser downloads your CSS, images, and JavaScript. That's slow and wastes bandwidth.

**The solution:** Tell browsers to cache static files. Once downloaded, they're stored locally and reused on future visits.

**How caching works:**

1. Browser requests `/styles.css`
2. Server sends the file with a header: "Cache this for 1 year"
3. Browser stores it locally
4. Next visit: browser uses the cached copy, no download needed

**Setting it up:**

```python
# pynext.config.py

# Cache static files for 1 year (in seconds)
# 31536000 = 60 × 60 × 24 × 365
static_cache_max_age = 31536000

# The full cache-control header
static_cache_control = "public, max-age=31536000, immutable"
```

**What the header parts mean:**

| Part | Meaning |
|------|---------|
| `public` | Can be cached by browsers and CDNs |
| `max-age=31536000` | Cache for 1 year |
| `immutable` | File will never change (browser skips revalidation) |

**But what if I change a file?** If you change `styles.css`, users will still see the old cached version! The solution is **cache busting**: add a version or hash to the filename:

```html
<!-- Instead of this -->
<link href="/styles.css">

<!-- Do this -->
<link href="/styles.abc123.css">
```

When you change the file, the filename changes, so browsers fetch the new version. PyNext's build process handles this automatically in production.

---

## Build Options

When you're ready to deploy your app to production, you'll run `pynext build`. This command takes your development code and transforms it into optimized, production-ready files. The build options control how this transformation happens.

### Where Build Output Goes

All generated files go into a build directory. By default, this is `.pynext/build/`:

```
my-app/
├── pages/
├── public/
├── .pynext/
│   └── build/              ← Production files go here
│       ├── static/
│       ├── bundles/
│       └── manifest.json
└── pynext.config.py
```

**Customizing the location:**

```python
# pynext.config.py

build_dir = ".pynext/build"      # The default
# Or put it somewhere else
build_dir = "dist"               # Common alternative
```

---

### Minification: Shrinking Your Code

**What is minification?** It's the process of removing unnecessary characters from code without changing its functionality — spaces, line breaks, comments, and long variable names are all stripped out.

**Before minification:**
```javascript
function calculateTotal(items) {
    // Sum all item prices
    let total = 0;
    for (const item of items) {
        total += item.price;
    }
    return total;
}
```

**After minification:**
```javascript
function calculateTotal(e){let t=0;for(const l of e)t+=l.price;return t}
```

**The result:** Your JavaScript files become 50-70% smaller, which means faster downloads for users.

**Setting it up:**

```python
# pynext.config.py

# Turn minification on (recommended for production)
minify = True

# Fine-tune what gets minified
minify_options = {
    "js": True,           # Minify JavaScript
    "css": True,          # Minify CSS
    "html": True,         # Minify HTML
    "remove_comments": True,
    "collapse_whitespace": True
}
```

**Pro tip:** Leave minification off during development so you can read the code in browser DevTools.

---

### Source Maps: Debugging Minified Code

**The problem:** When something breaks in production, the error points to line 1, column 34892 of a single minified file. That's impossible to debug!

**The solution:** Source maps are files that map the minified code back to your original source code. With source maps, browser DevTools show your original files.

**Setting it up:**

```python
# pynext.config.py

# Generate source maps (recommended for development, optional for production)
source_maps = True

# Where to put the source map
source_map_style = "inline"    # Include in the JS file itself
# Or
source_map_style = "external"  # Separate .map file
# Or
source_map_style = "both"      # Both inline and external
```

**Production considerations:** Source maps reveal your original code. If that's sensitive, either:
- Don't generate source maps for production (`source_maps = False`)
- Generate external maps and only upload them to an error tracking service (like Sentry), not your public server

---

### Asset Optimization: Smaller Images, Faster Sites

**What gets optimized?** Images are often the largest files on a website. PyNext can automatically compress and convert them to modern formats during the build.

**The benefits:**
| Format | Compared to JPEG | Browser Support |
|--------|------------------|-----------------|
| WebP | 25-35% smaller | All modern browsers |
| AVIF | 50% smaller | Chrome, Firefox, Safari 16+ |

**Setting it up:**

```python
# pynext.config.py

# Enable asset optimization
optimize_assets = True

# Image-specific settings
optimize_images = True
image_quality = 85              # Quality level (1-100, higher = larger file)
image_formats = ["webp", "avif"]  # Convert to these formats

# CSS optimization
optimize_css = True
autoprefixer = True             # Add -webkit-, -moz- prefixes automatically
```

**What happens during build:**

1. PyNext scans your `public/` folder for images
2. Each image is compressed and converted to WebP and AVIF
3. The HTML is updated to use `<picture>` tags with fallbacks:

```html
<picture>
    <source srcset="/images/hero.avif" type="image/avif">
    <source srcset="/images/hero.webp" type="image/webp">
    <img src="/images/hero.jpg" alt="Hero">
</picture>
```

---

### Code Splitting: Loading Only What You Need

**The problem:** If all your JavaScript is in one file, users download everything upfront — even code for pages they'll never visit.

**The solution:** Code splitting divides your code into smaller "chunks." Each page only loads the code it needs.

**How it works:**

```
Without splitting:                With splitting:
┌─────────────────────┐          ┌──────────────┐
│   bundle.js (500KB) │          │ shared.js    │ (utilities, 50KB)
│                     │          ├──────────────┤
│ - Home page code    │    →     │ home.js      │ (20KB)
│ - Dashboard code    │          ├──────────────┤
│ - Settings code     │          │ dashboard.js │ (30KB)
│ - All utilities     │          ├──────────────┤
└─────────────────────┘          │ settings.js  │ (15KB)
                                 └──────────────┘
```

Now visiting the home page downloads 70KB (shared + home) instead of 500KB.

**Setting it up:**

```python
# pynext.config.py

# Enable code splitting (recommended)
code_splitting = True

# Split third-party code into a separate vendor chunk
vendor_splitting = True

# Don't create chunks smaller than this (too many small files = slow)
chunk_size_limit = 50000        # 50KB minimum
```

**Pro tip:** Code splitting works best with lazy loading (see the [Code Splitting guide](../optimization/CODE_SPLITTING.md) for details).

---

## Development Settings

These settings make your development experience smoother — automatic reloading when you change files, helpful error messages, and detailed logging.

### Hot Reload: See Changes Instantly

**What is hot reload?** When you save a file, PyNext automatically detects the change and reloads your application. You don't have to stop and restart the server manually.

**How it works:**

1. You edit `pages/index.py` and save
2. PyNext sees the file changed (within 100ms)
3. The server reloads that module
4. Your browser refreshes (or just updates the changed part)

**The experience:** Save your code, glance at the browser, see your changes. It feels almost instant.

**Setting it up:**

```python
# pynext.config.py

# Enable hot reload (on by default during development)
hot_reload = True

# Which folders to watch for changes
watch_dirs = [
    "pages",        # Your page components
    "components",   # Reusable components
    "public"        # Static files (CSS, images)
]

# Files to ignore (these won't trigger reload)
watch_ignore = [
    "*.pyc",            # Compiled Python
    "__pycache__",      # Python cache folder
    ".git",             # Git internals
    "node_modules"      # npm packages (too many files!)
]

# Wait this long after a change before reloading
# (prevents multiple reloads when saving multiple files)
watch_debounce = 100    # milliseconds
```

**Troubleshooting:** If hot reload seems slow or isn't working:
- Check that the file is in a watched directory
- Make sure it's not in the ignore list
- Large `node_modules` folders can slow down file watching

---

### Auto-Open Browser

Tired of typing `localhost:3000` every time you start the server? PyNext can open the browser for you:

```python
# pynext.config.py

# Open browser when server starts
open_browser = True

# Which browser to use
browser = "default"     # Uses your system default
# Or specify:
browser = "chrome"
browser = "firefox"
browser = "safari"
```

This is purely a convenience feature — it just saves you a click.

---

### Logging: Understanding What's Happening

**Why logging matters:** When something goes wrong (or even when it goes right), logs tell you what happened. They're essential for debugging.

**Log levels explained:**

| Level | What it shows | When to use |
|-------|---------------|-------------|
| `DEBUG` | Everything (every request, every detail) | Development |
| `INFO` | General events (server started, user logged in) | Production |
| `WARNING` | Something unexpected but handled | Always useful |
| `ERROR` | Something broke | Always useful |

**Setting it up:**

```python
# pynext.config.py

# How much detail to log
log_level = "DEBUG"      # During development, see everything

# For production, use INFO (less noise)
log_level = "INFO"

# Customize the format (optional)
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# This produces: "2024-01-15 10:30:45 - pynext - INFO - Server started"

# Save logs to a file (optional)
log_file = "logs/pynext.log"

# Log every HTTP request?
log_requests = True

# Include request bodies in logs? (careful with passwords!)
log_request_body = False
```

**Example log output:**
```
2024-01-15 10:30:45 - pynext - INFO - Starting development server
2024-01-15 10:30:45 - pynext - INFO - Listening on http://localhost:3000
2024-01-15 10:30:47 - pynext - DEBUG - GET / 200 OK (12ms)
2024-01-15 10:30:48 - pynext - DEBUG - GET /api/users 200 OK (45ms)
2024-01-15 10:30:52 - pynext - WARNING - Slow request: /api/heavy-query took 2.3s
```

---

### Error Display: Helpful Error Pages

**The development experience:** When something crashes, you want to know exactly what went wrong — the error message, the stack trace, and ideally the actual code that caused it.

**Setting it up:**

```python
# pynext.config.py

# Show detailed error information (development only!)
show_error_details = True

# Show the actual source code in error pages
show_source_code = True

# How many lines of code to show around the error
source_code_context_lines = 5

# Use a custom error template (optional)
error_template = "errors/500.html"
```

**What you see when an error occurs:**

```
╔══════════════════════════════════════════════════════════════╗
║  TypeError: 'NoneType' object is not subscriptable           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  File: pages/dashboard.py, line 23                           ║
║                                                              ║
║     21 │   user = get_current_user()                         ║
║     22 │                                                     ║
║  →  23 │   return div()[f"Hello, {user['name']}"]           ║
║     24 │                                                     ║
║     25 │ @component                                          ║
║                                                              ║
║  The variable 'user' is None. Did you forget to check       ║
║  if the user is logged in?                                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**Security warning:** Never enable `show_error_details` in production! It exposes your code and can reveal sensitive information. Set it based on environment:

```python
import os

show_error_details = os.getenv("PYNEXT_ENV") != "production"
```

---

## Production Settings

Going to production is a big step. Your development settings (debug mode, verbose logging, no caching) are great for building, but terrible for real users. This section explains how to configure PyNext for production.

### The Development → Production Mindset Shift

| Concern | Development | Production |
|---------|-------------|------------|
| **Errors** | Show everything (stack traces, code) | Show generic error page |
| **Performance** | Not important | Critical |
| **Security** | Relaxed | Locked down |
| **Logging** | Verbose (DEBUG) | Essential only (INFO/WARNING) |
| **Caching** | Disabled (always fresh) | Aggressive (fast) |

---

### A Complete Production Configuration

Here's a production-ready config that handles the switch automatically based on an environment variable:

```python
# pynext.config.py

import os

# ─────────────────────────────────────────────────────────────────
# ENVIRONMENT DETECTION
# ─────────────────────────────────────────────────────────────────
# Set PYNEXT_ENV=production in your deployment environment
ENV = os.getenv("PYNEXT_ENV", "development")
IS_PROD = ENV == "production"

# ─────────────────────────────────────────────────────────────────
# SERVER
# ─────────────────────────────────────────────────────────────────
# In production: listen on all interfaces (required for Docker/cloud)
# In development: only localhost (safer)
host = "0.0.0.0" if IS_PROD else "localhost"

# Allow PORT to be set by the hosting platform (Heroku, Railway, etc.)
port = int(os.getenv("PORT", 3000))

# Debug mode: NEVER in production
debug = not IS_PROD

# Multiple workers in production for handling concurrent requests
workers = (os.cpu_count() or 1) * 2 + 1 if IS_PROD else 1

# ─────────────────────────────────────────────────────────────────
# SECURITY
# ─────────────────────────────────────────────────────────────────
# Secret key for signing cookies and tokens
# NEVER use the default in production!
secret_key = os.getenv("SECRET_KEY", "dev-secret-CHANGE-THIS-IN-PRODUCTION")

# ─────────────────────────────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────────────────────────────
# In production: cache for 1 year (with cache busting via filenames)
# In development: no caching (always fresh)
static_cache_max_age = 31536000 if IS_PROD else 0

# ─────────────────────────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────────────────────────
# Minify in production for smaller files
minify = IS_PROD

# Source maps help debugging but expose code
source_maps = not IS_PROD

# ─────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────
# In production: less noise
# In development: see everything
log_level = "INFO" if IS_PROD else "DEBUG"

# Never show detailed errors in production
show_error_details = not IS_PROD
```

**How to use this:** In your deployment platform, set the environment variable:

```bash
PYNEXT_ENV=production
SECRET_KEY=your-actual-secret-key-here
```

---

### Security Settings: Protecting Your App

**CORS (Cross-Origin Resource Sharing):** Controls which other websites can make requests to your API. Without CORS restrictions, any website could call your API and potentially steal user data.

```python
# pynext.config.py

# Enable CORS controls
cors_enabled = True

# Which origins can access your API
cors_origins = [
    "https://example.com",           # Your main site
    "https://www.example.com",       # WWW version
    "https://admin.example.com"      # Admin subdomain
]

# Which HTTP methods are allowed
cors_methods = ["GET", "POST", "PUT", "DELETE"]

# Which headers clients can send
cors_headers = ["Content-Type", "Authorization"]

# Allow credentials (cookies) in cross-origin requests
cors_credentials = True
```

**CSRF (Cross-Site Request Forgery) Protection:** Prevents attackers from tricking users into performing actions they didn't intend. This is especially important for forms that change data.

```python
# pynext.config.py

# Enable CSRF protection
csrf_enabled = True

# Name of the cookie that holds the CSRF token
csrf_cookie_name = "csrf_token"

# Name of the header that must contain the token
csrf_header_name = "X-CSRF-Token"
```

**Security Headers:** These tell browsers to enable various security features:

```python
# pynext.config.py

security_headers = {
    # Prevent browsers from guessing content types
    "X-Content-Type-Options": "nosniff",
    
    # Prevent your site from being embedded in iframes (clickjacking protection)
    "X-Frame-Options": "DENY",
    
    # Enable browser's XSS filter
    "X-XSS-Protection": "1; mode=block",
    
    # Force HTTPS for 1 year
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}
```

**Allowed Hosts:** Prevents host header attacks by only accepting requests for known hostnames:

```python
# pynext.config.py

allowed_hosts = [
    "example.com",
    "www.example.com"
]
```

---

### SSL/TLS: HTTPS Support

**Most deployments don't need this:** If you're using a reverse proxy (nginx, Cloudflare, AWS ALB), the proxy handles SSL and passes plain HTTP to PyNext. This is the recommended setup.

**When you might need it:** If PyNext is directly facing the internet without a proxy:

```python
# pynext.config.py
import os

ssl_enabled = True
ssl_cert = os.getenv("SSL_CERT_PATH", "/etc/letsencrypt/live/example.com/fullchain.pem")
ssl_key = os.getenv("SSL_KEY_PATH", "/etc/letsencrypt/live/example.com/privkey.pem")
```

**Pro tip:** For most deployments, use a reverse proxy or cloud load balancer to handle SSL. It's easier to manage certificates and offloads encryption work from your app.

---

## Environment Variables

Hard-coding secrets (database passwords, API keys) in your config file is dangerous — anyone who sees your code sees your secrets. Environment variables solve this by keeping sensitive values outside your code.

### The Problem with Hard-Coded Secrets

```python
# ❌ DON'T DO THIS!
database_url = "postgresql://admin:super_secret_password@db.example.com/mydb"
stripe_api_key = "sk_live_abc123xyz"
```

If this code ends up on GitHub (even in a private repo), your secrets are exposed. If an attacker gets access to your code, they get your database.

### The Solution: Environment Variables

Environment variables are values set outside your code, in the operating system or deployment platform. Your code reads them at runtime:

```python
# ✅ DO THIS
import os

database_url = os.getenv("DATABASE_URL")
stripe_api_key = os.getenv("STRIPE_API_KEY")
```

Now the secrets live in your server's environment, not in code.

---

### Step 1: Create a `.env` File for Development

During development, you don't want to set environment variables manually every time. The `.env` file is a convenient way to define them locally:

```bash
# .env
#
# This file contains secrets for LOCAL DEVELOPMENT ONLY.
# NEVER commit this to git!

# Server settings
PYNEXT_ENV=development
PORT=3000
SECRET_KEY=dev-secret-key-for-local-testing-only

# Database
DATABASE_URL=postgresql://localhost/myapp_dev

# External APIs
STRIPE_API_KEY=sk_test_xxxxxxxxxxxxxxx
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxx

# Feature flags
ENABLE_BETA_FEATURES=true
```

**Important:** Add `.env` to your `.gitignore` so it never gets committed:

```bash
# .gitignore
.env
.env.local
.env.*.local
```

---

### Step 2: Load the `.env` File in Your Config

The `python-dotenv` package reads `.env` files and loads them as environment variables:

```python
# pynext.config.py

import os
from dotenv import load_dotenv

# Load .env file (if it exists)
# This makes the values available via os.getenv()
load_dotenv()

# Now use the environment variables
secret_key = os.getenv("SECRET_KEY")
database_url = os.getenv("DATABASE_URL")

# For booleans, you need to convert from string
debug = os.getenv("DEBUG", "false").lower() == "true"

# For integers, convert the type
port = int(os.getenv("PORT", "3000"))
```

**Installing python-dotenv:**

```bash
pip install python-dotenv
```

(Or add `python-dotenv` to your `pynext.requirements.txt`)

---

### Step 3: Handle Multiple Environments

You might have different settings for development, staging, and production. Here's how to organize that:

**File structure:**

```
my-app/
├── .env                  # Shared defaults
├── .env.development      # Development overrides
├── .env.staging          # Staging overrides
├── .env.production       # Production overrides (NOT committed!)
├── .env.local            # Your personal overrides (NOT committed!)
└── pynext.config.py
```

**Loading order (later files override earlier):**

```python
# pynext.config.py

from dotenv import load_dotenv
import os

# Which environment are we in?
env = os.getenv("PYNEXT_ENV", "development")

# Load files in order (each can override the previous)
load_dotenv(".env")                # Base defaults
load_dotenv(f".env.{env}")         # Environment-specific
load_dotenv(".env.local")          # Personal overrides (highest priority)
```

**Example files:**

```bash
# .env (committed - contains non-sensitive defaults)
PORT=3000
LOG_LEVEL=INFO

# .env.development (committed - dev-specific)
DEBUG=true
LOG_LEVEL=DEBUG

# .env.production (NOT committed - production secrets)
SECRET_KEY=real-production-secret
DATABASE_URL=postgresql://prod-server/myapp

# .env.local (NOT committed - your personal tweaks)
PORT=3001  # I like using 3001 locally
```

---

### Step 4: Using Environment Variables for Different Settings

**Pattern: Environment-based configuration:**

```python
# pynext.config.py

import os
from dotenv import load_dotenv

load_dotenv()

# Detect environment
ENV = os.getenv("PYNEXT_ENV", "development")
IS_PROD = ENV == "production"
IS_DEV = ENV == "development"

# Settings that change per environment
debug = IS_DEV
minify = IS_PROD
log_level = "INFO" if IS_PROD else "DEBUG"

# Settings from environment variables (with safe defaults)
secret_key = os.getenv("SECRET_KEY", "unsafe-dev-key")
database_url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Validate required settings in production
if IS_PROD:
    if secret_key == "unsafe-dev-key":
        raise ValueError("SECRET_KEY must be set in production!")
    if "sqlite" in database_url:
        raise ValueError("Don't use SQLite in production!")
```

---

### Priority: What Overrides What?

When the same variable is set in multiple places, here's the priority (highest to lowest):

1. **System environment variables** (set in terminal or deployment platform)
2. **`.env.local`** (your personal overrides)
3. **`.env.{environment}`** (e.g., `.env.production`)
4. **`.env`** (base defaults)

**Example:** If `PORT=3000` in `.env` but you run `PORT=8080 pynext dev`, the app uses port 8080.

---

### Setting Environment Variables in Production

**On Linux/Mac (terminal):**
```bash
export PYNEXT_ENV=production
export SECRET_KEY=your-secret-here
pynext start
```

**In Docker:**
```dockerfile
ENV PYNEXT_ENV=production
ENV SECRET_KEY=your-secret-here
```

**In Heroku:**
```bash
heroku config:set PYNEXT_ENV=production SECRET_KEY=your-secret-here
```

**In Railway/Render/Vercel:**
Use their dashboard to add environment variables.

**Pro tip:** Never put production secrets in `.env.production` in your repo. Set them directly in your hosting platform's environment variable settings.

---

## Advanced Configuration

These settings are for power users who need to customize PyNext beyond the standard options. Most projects won't need these.

---

### Custom Middleware: Intercepting Every Request

**What is middleware?** Middleware is code that runs on every request, before your page code executes. It's useful for things like:
- Compressing responses (gzip)
- Adding security headers
- Logging
- Authentication checks

**How it works:**

```
Request → Middleware 1 → Middleware 2 → Your Page → Middleware 2 → Middleware 1 → Response
```

Each middleware can modify the request going in or the response going out.

**Adding middleware:**

```python
# pynext.config.py

from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware

# List of middleware to apply to all requests
middleware = [
    # Compress responses larger than 1000 bytes
    Middleware(GZipMiddleware, minimum_size=1000),
    
    # Add your custom middleware classes here
]
```

**Creating your own middleware:**

```python
# my_middleware.py

from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        import time
        start = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response
```

```python
# pynext.config.py

from starlette.middleware import Middleware
from my_middleware import TimingMiddleware

middleware = [
    Middleware(TimingMiddleware),
]
```

---

### Custom Routes: Beyond File-Based Routing

**When do you need this?** PyNext's file-based routing handles most cases. But sometimes you need:
- A health check endpoint for load balancers
- A metrics endpoint for monitoring
- Legacy routes that don't fit the file structure

**Adding custom routes:**

```python
# pynext.config.py

custom_routes = [
    # Health check for load balancers (returns 200 OK)
    {"path": "/health", "handler": "handlers.health_check"},
    
    # Prometheus metrics endpoint
    {"path": "/metrics", "handler": "handlers.prometheus_metrics"},
    
    # Legacy redirect
    {"path": "/old-page", "redirect": "/new-page"}
]
```

**The handler file:**

```python
# handlers.py

from fastapi import Response

async def health_check():
    return Response("OK", status_code=200)

async def prometheus_metrics():
    # Return Prometheus-formatted metrics
    return Response(
        "requests_total 12345\nresponse_time_seconds 0.045",
        media_type="text/plain"
    )
```

**API prefix:** If you want all your API routes under a prefix:

```python
# pynext.config.py

api_prefix = "/api/v1"

# Now pages/api/users/route.py is available at /api/v1/users
# instead of /api/users
```

---

### Plugin System: Extending PyNext

**What are plugins?** Plugins are reusable packages that add functionality to PyNext — authentication, admin panels, caching, etc.

**Using plugins:**

```python
# pynext.config.py

plugins = [
    # Just the plugin name (uses default config)
    "pynext_auth",
    
    # With configuration
    {"pynext_cache": {
        "backend": "redis",
        "url": "redis://localhost:6379"
    }},
    
    # Multiple plugins
    "pynext_admin",
    "pynext_analytics",
]
```

**Note:** The plugin system is designed for the PyNext ecosystem. Check the [PyNext Plugins](https://pynext.dev/plugins) page for available plugins.

---

### Database Configuration: Connecting to Data

**When do you need this?** If your Server Actions query a database, you can configure connection pooling here.

**Why connection pooling?** Opening a new database connection for every request is slow. Connection pooling maintains a set of open connections that requests can reuse.

```python
# pynext.config.py

import os

# PostgreSQL/MySQL configuration
database = {
    # Connection URL (from environment variable)
    "url": os.getenv("DATABASE_URL", "postgresql://localhost/myapp"),
    
    # Pool settings
    "pool_size": 20,        # Number of connections to keep open
    "max_overflow": 10,     # Extra connections allowed during spikes
    "pool_pre_ping": True,  # Test connections before using (catches stale connections)
}

# Redis configuration (for caching, sessions, etc.)
redis = {
    "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "db": 0,                # Redis database number (0-15)
}
```

**Using in your Server Actions:**

```python
from pynext import server_action
from pynext.database import get_db  # Provided by PyNext

@server_action
async def get_users():
    async with get_db() as db:
        result = await db.execute("SELECT * FROM users")
        return result.fetchall()
```

---

### Template Settings: Customizing HTML Output

**What is this?** Every page PyNext renders is wrapped in an HTML document. These settings control the wrapper.

```python
# pynext.config.py

page_template = {
    # The DOCTYPE declaration
    "doctype": "<!DOCTYPE html>",
    
    # Attributes on the <html> tag
    "html_attrs": {
        "lang": "en",
        "dir": "ltr"       # "ltr" or "rtl" for right-to-left languages
    },
    
    # Default <meta> tags (added to every page)
    "default_meta": [
        {"charset": "utf-8"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        {"name": "theme-color", "content": "#6366f1"}
    ],
    
    # Default content in <head> (added to every page)
    "default_head": [
        '<link rel="icon" href="/favicon.ico">',
        '<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
    ]
}
```

**Result:**

```html
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#6366f1">
    <link rel="icon" href="/favicon.ico">
    <link rel="apple-touch-icon" href="/apple-touch-icon.png">
    <!-- Your page's head content -->
</head>
<body>
    <!-- Your page content -->
</body>
</html>
```

---

## Complete Reference

This section provides a quick-reference table of all configuration options and a complete example config file you can copy and customize.

### Quick Reference Table

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| **Server** ||||
| `host` | str | `"localhost"` | Network interface to bind to |
| `port` | int | `3000` | Port to listen on |
| `debug` | bool | `True` | Enable debug mode |
| `workers` | int | `1` | Number of worker processes |
| `request_timeout` | int | `30` | Request timeout (seconds) |
| **Routing** ||||
| `pages_dir` | str | `"pages"` | Directory containing page files |
| `base_path` | str | `""` | URL prefix for all routes |
| **Static Files** ||||
| `static_dir` | str | `"public"` | Static files directory |
| `static_url` | str | `"/"` | URL prefix for static files |
| `static_cache_max_age` | int | `0` | Cache duration (seconds) |
| **Build** ||||
| `build_dir` | str | `".pynext/build"` | Build output directory |
| `minify` | bool | `False` | Minify JavaScript/CSS |
| `source_maps` | bool | `True` | Generate source maps |
| `code_splitting` | bool | `True` | Enable code splitting |
| **Development** ||||
| `hot_reload` | bool | `True` | Enable hot reload |
| `open_browser` | bool | `False` | Open browser on start |
| `watch_dirs` | list | `["pages", ...]` | Directories to watch |
| **Logging** ||||
| `log_level` | str | `"DEBUG"` | Logging level |
| `log_requests` | bool | `True` | Log HTTP requests |
| `show_error_details` | bool | `True` | Show detailed errors |
| **Security** ||||
| `secret_key` | str | (required) | Secret key for signing |
| `cors_enabled` | bool | `True` | Enable CORS |
| `cors_origins` | list | `["*"]` | Allowed origins |
| `csrf_enabled` | bool | `False` | Enable CSRF protection |
| `allowed_hosts` | list | `["*"]` | Allowed host headers |

---

### Complete Example Configuration

Here's a production-ready configuration file you can use as a starting point. It automatically adjusts settings based on the `PYNEXT_ENV` environment variable:

```python
# pynext.config.py - Complete Production-Ready Configuration
#
# Copy this file and customize for your project.
# Set PYNEXT_ENV=production in your deployment environment.

import os

# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================
# This pattern lets you use the same config file for development and production
ENV = os.getenv("PYNEXT_ENV", "development")
IS_PROD = ENV == "production"
IS_DEV = ENV == "development"

# =============================================================================
# SERVER SETTINGS
# =============================================================================
# Development: only accessible from your machine
# Production: accessible from network (required for Docker/cloud)
host = "0.0.0.0" if IS_PROD else "localhost"

# Allow the port to be set by environment (many hosting platforms do this)
port = int(os.getenv("PORT", 3000))

# Debug mode: helpful during development, dangerous in production
debug = IS_DEV

# Workers: multiple processes in production for concurrency
# Rule of thumb: (CPU cores × 2) + 1
workers = (os.cpu_count() or 1) * 2 + 1 if IS_PROD else 1

# Timeouts (in seconds)
request_timeout = 30      # How long a request can take
keep_alive = 5            # Keep connections open for reuse
shutdown_timeout = 30     # Time to finish requests when stopping

# =============================================================================
# ROUTING
# =============================================================================
pages_dir = "pages"       # Where your page files live
base_path = ""            # URL prefix (e.g., "/app" → /app/page)

# =============================================================================
# STATIC FILES
# =============================================================================
static_dir = "public"
static_url = "/"

# In production: cache for 1 year (files have hashed names)
# In development: no caching (always fresh)
static_cache_max_age = 31536000 if IS_PROD else 0

# =============================================================================
# BUILD SETTINGS
# =============================================================================
build_dir = ".pynext/build"

# Minify in production for smaller files
minify = IS_PROD

# Source maps in development for debugging
source_maps = IS_DEV

# Code splitting for faster page loads
code_splitting = True

# =============================================================================
# DEVELOPMENT SETTINGS
# =============================================================================
# Auto-reload when files change
hot_reload = IS_DEV

# Open browser automatically
open_browser = False

# Which directories trigger hot reload
watch_dirs = ["pages", "components", "public"]

# Files to ignore
watch_ignore = ["*.pyc", "__pycache__", ".git", "node_modules"]

# =============================================================================
# LOGGING
# =============================================================================
# Production: less noise, development: see everything
log_level = "INFO" if IS_PROD else "DEBUG"
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_requests = True

# Detailed errors in development only (security risk in production)
show_error_details = IS_DEV

# =============================================================================
# SECURITY
# =============================================================================
# IMPORTANT: Set a real secret key in production!
secret_key = os.getenv("SECRET_KEY", "dev-only-change-in-production")

# Validate secret key in production
if IS_PROD and secret_key.startswith("dev"):
    raise ValueError("You must set a real SECRET_KEY in production!")

# CORS (Cross-Origin Resource Sharing)
cors_enabled = True
cors_origins = ["*"] if IS_DEV else [
    os.getenv("FRONTEND_URL", "https://example.com")
]
cors_methods = ["GET", "POST", "PUT", "DELETE"]
cors_credentials = True

# CSRF Protection (for form submissions)
csrf_enabled = IS_PROD

# Allowed hosts (prevents host header attacks)
allowed_hosts = ["*"] if IS_DEV else [
    os.getenv("ALLOWED_HOST", "example.com"),
    "www." + os.getenv("ALLOWED_HOST", "example.com")
]

# SSL (usually handled by reverse proxy, not needed here)
ssl_enabled = False
ssl_cert = os.getenv("SSL_CERT_PATH")
ssl_key = os.getenv("SSL_KEY_PATH")
```

---

### Adding Type Hints for IDE Support

If you want better autocomplete and error checking in your IDE, you can add type hints:

```python
# pynext.config.py

from typing import List, Dict, Union

# With type hints, your IDE knows what types each setting expects
host: str = "localhost"
port: int = 3000
debug: bool = True
workers: int = 4

npm_packages: List[Union[str, Dict[str, str]]] = [
    "chart.js",
    {"lodash": "^4.17.0"}
]

cors_origins: List[str] = ["https://example.com"]
```

---

### Validating Configuration with Pydantic

**Why validate?** Catching configuration errors at startup is much better than discovering them when a user hits an error in production. Pydantic lets you define rules that your configuration must follow.

```python
# pynext.config.py

from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    """
    Configuration with validation.
    
    Pydantic will:
    - Load values from environment variables automatically
    - Convert types (PORT="3000" becomes int 3000)
    - Run validators to check values
    - Raise clear errors if something is wrong
    """
    
    host: str = "localhost"
    port: int = 3000
    debug: bool = True
    secret_key: str  # Required - no default!
    
    @validator("port")
    def port_must_be_valid(cls, v):
        """Ensure port is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("secret_key")
    def secret_key_must_be_strong(cls, v):
        """Ensure secret key is long enough."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        return v
    
    class Config:
        # Automatically read from .env file
        env_file = ".env"

# This runs validation immediately when the config loads
# If anything is wrong, you'll see the error on startup
settings = Settings()

# Export for PyNext
host = settings.host
port = settings.port
debug = settings.debug
secret_key = settings.secret_key
```

**What happens with invalid config:**

```bash
$ pynext dev
pydantic.error_wrappers.ValidationError: 1 validation error for Settings
secret_key
  Secret key must be at least 32 characters (type=value_error)
```

Clear error, immediate feedback, before any requests are served.

---

## CLI Configuration Override

Sometimes you need to temporarily change a setting without editing the config file. PyNext's CLI accepts flags that override your config:

**Overriding server settings:**

```bash
# Use a different port (maybe 3000 is taken)
pynext dev --port 8080

# Listen on all interfaces (for testing from another device)
pynext dev --host 0.0.0.0

# Both at once
pynext dev --host 0.0.0.0 --port 8080
```

**Controlling dependencies:**

```bash
# Skip dependency checking (faster startup)
pynext dev --skip-deps

# Check but don't auto-install
pynext dev --no-install
```

**Setting the environment:**

```bash
# Run with production settings
PYNEXT_ENV=production pynext start

# Run build with production optimizations
PYNEXT_ENV=production pynext build
```

**Using a different config file:**

```bash
# Use a custom config (for testing, staging, etc.)
pynext dev --config ./configs/staging.config.py
```

**Priority:** CLI flags override environment variables, which override the config file, which overrides defaults.

```
CLI flags  →  Environment variables  →  pynext.config.py  →  Defaults
(highest)                                                    (lowest)
```

---

## Summary: What You've Learned

Congratulations! You now understand how to configure a PyNext application:

| Topic | What you learned |
|-------|------------------|
| **Dependency Files** | `pynext.requirements.txt` for Python, `pynext.npm.txt` for JavaScript |
| **Server Settings** | Host, port, workers, timeouts |
| **Static Files** | Serving images, CSS, and other assets |
| **Build Options** | Minification, source maps, code splitting |
| **Development** | Hot reload, logging, error display |
| **Production** | Security settings, CORS, CSRF, SSL |
| **Environment Variables** | Keeping secrets out of code |
| **Advanced** | Middleware, plugins, database pooling |

---

## Next Steps

Now that your app is configured, explore these guides:

| If you want to... | Read this |
|-------------------|-----------|
| Create your first page | [Getting Started](./GETTING_STARTED.md) |
| Understand URL routing | [Routing](../routing/ROUTING.md) |
| Call Python from the browser | [Server Actions](../data/SERVER_ACTIONS.md) |
| Add reactive state | [State Management](../state/STATE_MANAGEMENT.md) |
| Deploy to production | [Deployment](../getting-started/DEPLOYMENT.md) |

