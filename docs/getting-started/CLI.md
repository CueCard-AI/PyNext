# CLI Reference

PyNext provides a command-line interface for project scaffolding, development, and production builds.

## Table of Contents

- [Installation](#installation)
- [Commands Overview](#commands-overview)
- [pynext init](#pynext-init)
- [pynext dev](#pynext-dev)
- [pynext build](#pynext-build)
- [pynext start](#pynext-start)
- [Global Options](#global-options)
- [Environment Variables](#environment-variables)
- [Exit Codes](#exit-codes)
- [Troubleshooting](#troubleshooting)

---

## Installation

The CLI is installed automatically with PyNext:

```bash
pip install pynext
```

Verify installation:

```bash
pynext --version
# PyNext 0.1.0

pynext --help
# Shows all available commands
```

---

## Commands Overview

| Command | Description |
|---------|-------------|
| `pynext init` | Create a new PyNext project |
| `pynext dev` | Start development server with hot reload |
| `pynext build` | Build for production |
| `pynext start` | Start production server |

---

## pynext init

Create a new PyNext project with the recommended directory structure.

### Usage

```bash
pynext init <project-name> [options]
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `project-name` | Name of the project directory to create | Yes |

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--template` | `-t` | Project template to use | `default` |
| `--npm` | | Initialize with npm packages | `false` |
| `--git` | | Initialize git repository | `true` |
| `--no-git` | | Skip git initialization | |
| `--install` | `-i` | Install dependencies after creation | `true` |
| `--no-install` | | Skip dependency installation | |

### Templates

| Template | Description |
|----------|-------------|
| `default` | Basic setup with index page |
| `minimal` | Bare minimum structure |
| `dashboard` | Dashboard with charts and data tables |
| `blog` | Blog with markdown support |
| `api` | API-focused with server actions |

### Examples

```bash
# Basic project
pynext init my-app

# With dashboard template
pynext init my-dashboard --template dashboard

# With npm packages pre-configured
pynext init my-app --npm

# Skip git and dependencies
pynext init my-app --no-git --no-install
```

### Generated Structure

```
my-app/
├── pages/
│   ├── index.py              # Home page
│   └── about.py              # About page
├── components/
│   ├── __init__.py
│   └── layout.py             # Layout component
├── static/
│   ├── styles.css            # Global styles
│   └── favicon.ico           # Favicon
├── pynext.config.py          # Configuration
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore file
└── README.md                 # Project readme
```

### Post-Creation Steps

After running `pynext init`, the CLI will display:

```
✅ Created project: my-app

Next steps:
  cd my-app
  pip install -r requirements.txt
  pynext dev

Open http://localhost:3000 to see your app
```

---

## pynext dev

Start the development server with hot reload enabled.

### Usage

```bash
pynext dev [options]
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--port` | `-p` | Port to run the server on | `3000` |
| `--host` | `-h` | Host to bind to | `localhost` |
| `--debug` | `-d` | Enable debug mode | `true` |
| `--open` | `-o` | Open browser automatically | `false` |
| `--config` | `-c` | Path to config file | `pynext.config.py` |
| `--no-reload` | | Disable hot reload | |

### Examples

```bash
# Start with defaults
pynext dev

# Custom port
pynext dev --port 8080

# Listen on all interfaces
pynext dev --host 0.0.0.0

# Open browser automatically
pynext dev --open

# Custom config file
pynext dev --config ./custom.config.py

# Disable hot reload
pynext dev --no-reload
```

### Output

```
🚀 PyNext development server

   ➜  Local:   http://localhost:3000
   ➜  Network: http://192.168.1.100:3000

   Hot reload enabled
   Debug mode enabled
   
   Ready in 150ms

Watching for changes...
```

### Hot Reload Behavior

The dev server watches for changes in:

- `pages/` - Page files
- `components/` - Component files
- `static/` - Static assets
- `pynext.config.py` - Configuration

**What triggers a reload:**

| Change Type | Behavior |
|-------------|----------|
| Page file modified | Page recompiled, browser refreshed |
| Component modified | Dependent pages recompiled |
| Static file modified | Browser refreshed |
| Config modified | Full server restart |
| New file added | Route registered, browser refreshed |
| File deleted | Route removed, browser refreshed |

### Debug Features

When debug mode is enabled (`--debug`):

- Detailed error pages with stack traces
- Source code shown in error messages
- API documentation at `/_pynext/docs`
- OpenAPI spec at `/_pynext/openapi.json`
- Action registry at `/_pynext/debug/actions`

### Development URLs

| URL | Description |
|-----|-------------|
| `/` | Your application |
| `/_pynext/docs` | Interactive API documentation |
| `/_pynext/redoc` | Alternative API docs |
| `/_pynext/openapi.json` | OpenAPI specification |
| `/_pynext/debug/actions` | List registered server actions |

---

## pynext build

Build the application for production deployment.

### Usage

```bash
pynext build [options]
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output` | `-o` | Output directory | `.pynext/build` |
| `--minify` | `-m` | Minify JavaScript and CSS | `true` |
| `--no-minify` | | Skip minification | |
| `--sourcemap` | `-s` | Generate source maps | `false` |
| `--analyze` | `-a` | Analyze bundle sizes | `false` |
| `--config` | `-c` | Path to config file | `pynext.config.py` |

### Examples

```bash
# Standard production build
pynext build

# With source maps for debugging
pynext build --sourcemap

# Analyze bundle sizes
pynext build --analyze

# Custom output directory
pynext build --output ./dist

# Skip minification (faster build)
pynext build --no-minify
```

### Output

```
🔨 Building for production...

   Compiling pages...
   ✓ pages/index.py
   ✓ pages/about.py
   ✓ pages/users/[id].py
   
   Bundling npm packages...
   ✓ chart.js (45.2 KB)
   ✓ lodash (24.1 KB)
   
   Optimizing assets...
   ✓ static/styles.css (2.1 KB)
   
   Generating runtime...
   ✓ signals.js (8.3 KB)

✅ Build complete!

   Output: .pynext/build/
   Total size: 79.7 KB (gzipped: 28.4 KB)
   Build time: 1.2s
```

### Build Output Structure

```
.pynext/build/
├── pages/                    # Compiled pages
│   ├── index.html
│   ├── about.html
│   └── users/
│       └── [id].html
├── static/                   # Static assets
│   ├── styles.css
│   └── styles.css.map        # (if --sourcemap)
├── _pynext/                  # Framework assets
│   ├── runtime.js            # Hydration runtime
│   ├── runtime.js.map        # (if --sourcemap)
│   └── bundles/              # NPM bundles
│       ├── chart.js.bundle.js
│       └── lodash.bundle.js
├── manifest.json             # Build manifest
└── routes.json               # Route manifest
```

### Bundle Analysis

With `--analyze`, a report is generated:

```
📊 Bundle Analysis

   Package          Size      Gzipped   % of Total
   ─────────────────────────────────────────────────
   chart.js         45.2 KB   15.1 KB   56.7%
   lodash           24.1 KB    8.2 KB   30.2%
   runtime.js        8.3 KB    2.8 KB   10.4%
   styles.css        2.1 KB    0.8 KB    2.7%
   ─────────────────────────────────────────────────
   Total            79.7 KB   26.9 KB   100%

   💡 Suggestions:
   - Consider using lodash-es for tree shaking
   - chart.js could be lazy loaded

   Report saved to: .pynext/build/bundle-report.html
```

---

## pynext start

Start the production server.

### Usage

```bash
pynext start [options]
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--port` | `-p` | Port to run on | `3000` |
| `--host` | `-h` | Host to bind to | `0.0.0.0` |
| `--workers` | `-w` | Number of worker processes | `auto` |
| `--config` | `-c` | Path to config file | `pynext.config.py` |

### Examples

```bash
# Start production server
pynext start

# Custom port and workers
pynext start --port 8080 --workers 4

# Bind to specific host
pynext start --host 127.0.0.1
```

### Output

```
🚀 PyNext production server

   ➜  Running on: http://0.0.0.0:3000
   ➜  Workers: 4
   ➜  Mode: production

   Server ready
```

### Production Features

- Multiple worker processes for concurrency
- Graceful shutdown handling
- Request logging
- Health check endpoint at `/_pynext/health`
- No debug features exposed

### Recommended: Use Gunicorn/Uvicorn

For production, we recommend using a proper ASGI server:

```bash
# Using Uvicorn (single process)
uvicorn pynext.server:app --host 0.0.0.0 --port 8000

# Using Uvicorn with workers
uvicorn pynext.server:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn with Uvicorn workers
gunicorn pynext.server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

---

## Global Options

These options work with all commands:

| Option | Description |
|--------|-------------|
| `--help` | Show help message |
| `--version` | Show version number |
| `--verbose` | Enable verbose output |
| `--quiet` | Suppress non-error output |

### Examples

```bash
# Show help for any command
pynext --help
pynext init --help
pynext dev --help

# Version
pynext --version

# Verbose mode
pynext build --verbose
```

---

## Environment Variables

The CLI respects these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PYNEXT_ENV` | Environment mode | `development` |
| `PYNEXT_PORT` | Server port | `3000` |
| `PYNEXT_HOST` | Server host | `localhost` |
| `PYNEXT_DEBUG` | Enable debug mode | `true` (dev) |
| `PYNEXT_CONFIG` | Config file path | `pynext.config.py` |
| `PYNEXT_LOG_LEVEL` | Logging level | `INFO` |

### Usage

```bash
# Set environment
PYNEXT_ENV=production pynext start

# Custom port via environment
PYNEXT_PORT=8080 pynext dev

# Multiple variables
PYNEXT_ENV=production PYNEXT_PORT=80 pynext start
```

### .env File Support

Create a `.env` file in your project root:

```bash
# .env
PYNEXT_ENV=development
PYNEXT_PORT=3000
PYNEXT_DEBUG=true
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://localhost/mydb
```

---

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid arguments |
| `3` | Configuration error |
| `4` | Build error |
| `5` | Runtime error |

### Examples

```bash
# Check exit code
pynext build
echo $?  # 0 if successful

# Use in scripts
if pynext build; then
    echo "Build successful"
    pynext start
else
    echo "Build failed"
    exit 1
fi
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

```
Error: Port 3000 is already in use

Solutions:
1. Use a different port: pynext dev --port 3001
2. Find and kill the process using the port:
   lsof -i :3000
   kill -9 <PID>
```

#### Module Not Found

```
Error: No module named 'pynext'

Solutions:
1. Install PyNext: pip install pynext
2. Check virtual environment is activated
3. Reinstall: pip install -e .
```

#### Config File Not Found

```
Error: Configuration file not found: pynext.config.py

Solutions:
1. Create the config file
2. Specify path: pynext dev --config ./path/to/config.py
3. Run from project root directory
```

#### Build Fails

```
Error: Build failed - syntax error in pages/index.py

Solutions:
1. Check the file for syntax errors
2. Run: python -m py_compile pages/index.py
3. Check import statements
```

#### Hot Reload Not Working

```
Hot reload not detecting changes

Solutions:
1. Check file is in watched directory (pages/, components/)
2. Check file is not in .gitignore
3. Restart dev server
4. Check file system events: pynext dev --verbose
```

### Debug Mode

Enable verbose logging for debugging:

```bash
# Verbose output
pynext dev --verbose

# Debug logging
PYNEXT_LOG_LEVEL=DEBUG pynext dev
```

### Getting Help

```bash
# Command help
pynext --help
pynext <command> --help

# Check version
pynext --version

# Report issues
# https://github.com/yourusername/pynext/issues
```

---

## Command Cheatsheet

```bash
# Create new project
pynext init my-app

# Development
pynext dev                    # Start dev server
pynext dev -p 8080           # Custom port
pynext dev -o                # Open browser
pynext dev --host 0.0.0.0    # Network access

# Production
pynext build                  # Build for production
pynext build --analyze       # With bundle analysis
pynext start                 # Start production server
pynext start -w 4            # With 4 workers

# Help
pynext --help                # General help
pynext dev --help            # Command-specific help
```

---

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Create your first project
- [Configuration](CONFIGURATION.md) - Configure your project
- [Deployment](DEPLOYMENT.md) - Deploy to production

