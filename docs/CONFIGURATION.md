# Configuration Guide

PyNext uses a Python configuration file for flexible, type-safe configuration. This guide covers all available options.

## Table of Contents

- [Configuration File](#configuration-file)
- [Server Settings](#server-settings)
- [NPM Packages](#npm-packages)
- [Static Files](#static-files)
- [Build Options](#build-options)
- [Development Settings](#development-settings)
- [Production Settings](#production-settings)
- [Environment Variables](#environment-variables)
- [Advanced Configuration](#advanced-configuration)
- [Complete Reference](#complete-reference)

---

## Configuration File

### Location

Create `pynext.config.py` in your project root:

```
my-app/
├── pages/
├── components/
├── static/
├── pynext.config.py    ← Configuration file
└── requirements.txt
```

### Basic Structure

```python
# pynext.config.py

# Server settings
host = "localhost"
port = 3000
debug = True

# NPM packages
npm_packages = [
    "chart.js",
    "lodash"
]

# Static files
static_dir = "static"
static_url = "/static"
```

### Configuration Options Overview

| Category | Options |
|----------|---------|
| Server | `host`, `port`, `debug`, `workers` |
| NPM | `npm_packages`, `react_compat`, `bundle_dir` |
| Static | `static_dir`, `static_url` |
| Build | `build_dir`, `minify`, `source_maps` |
| Dev | `hot_reload`, `open_browser` |
| Routes | `pages_dir`, `base_path` |

---

## Server Settings

### Host and Port

```python
# pynext.config.py

# Network binding
host = "localhost"      # Default: localhost
port = 3000             # Default: 3000

# Listen on all interfaces
host = "0.0.0.0"        # Accessible from network

# Custom port
port = 8080
```

### Debug Mode

```python
# pynext.config.py

# Enable debug mode
debug = True            # Default: True in dev, False in prod

# Debug mode enables:
# - Detailed error pages
# - Hot reload
# - Verbose logging
# - API documentation at /_pynext/docs
```

### Workers (Production)

```python
# pynext.config.py

# Number of worker processes (production only)
workers = 4             # Default: (CPU cores * 2) + 1

# Auto-calculate based on CPU
import os
workers = os.cpu_count() * 2 + 1
```

### Timeouts

```python
# pynext.config.py

# Request timeout in seconds
request_timeout = 30    # Default: 30

# Keep-alive timeout
keep_alive = 5          # Default: 5

# Graceful shutdown timeout
shutdown_timeout = 30   # Default: 30
```

---

## NPM Packages

### Basic Usage

```python
# pynext.config.py

# List of npm packages to bundle
npm_packages = [
    "chart.js",         # Latest version
    "lodash",
    "dayjs"
]
```

### Version Pinning

```python
# pynext.config.py

npm_packages = [
    "chart.js",                      # Latest
    {"lodash": "^4.17.0"},           # Semver range
    {"dayjs": "1.11.10"},            # Exact version
    {"axios": ">=1.0.0 <2.0.0"}      # Range
]
```

### React Compatibility Mode

Enable Preact aliasing for React packages:

```python
# pynext.config.py

# Enable React → Preact aliasing
react_compat = True     # Default: False

# This replaces:
# - react → preact/compat
# - react-dom → preact/compat
# - react/jsx-runtime → preact/jsx-runtime

# Useful for packages like:
npm_packages = [
    "@mui/material",
    "react-query",
    "recharts"
]
```

### Bundle Directory

```python
# pynext.config.py

# Where to store bundled packages
bundle_dir = ".pynext/bundles"    # Default: .pynext/bundles
```

### Esbuild Options

```python
# pynext.config.py

# Custom esbuild configuration
esbuild_options = {
    "target": "es2020",           # JavaScript target
    "format": "esm",              # Output format
    "minify": True,               # Minify output
    "sourcemap": True,            # Generate source maps
    "splitting": True,            # Code splitting
    "tree_shaking": True,         # Remove unused code
}
```

### Package Aliases

```python
# pynext.config.py

# Custom import aliases
package_aliases = {
    "react": "preact/compat",
    "react-dom": "preact/compat",
    "@/": "./src/",               # Path alias
}
```

---

## Static Files

### Directory Configuration

```python
# pynext.config.py

# Static files directory
static_dir = "static"           # Default: static

# URL prefix for static files
static_url = "/static"          # Default: /static

# Example:
# File: static/styles.css
# URL:  /static/styles.css
```

### Multiple Static Directories

```python
# pynext.config.py

# Multiple static directories
static_dirs = [
    {"path": "static", "url": "/static"},
    {"path": "uploads", "url": "/uploads"},
    {"path": "assets", "url": "/assets"}
]
```

### File Caching

```python
# pynext.config.py

# Static file caching (production)
static_cache_max_age = 31536000  # 1 year in seconds

# Cache control headers
static_cache_control = "public, max-age=31536000, immutable"
```

---

## Build Options

### Build Directory

```python
# pynext.config.py

# Build output directory
build_dir = ".pynext/build"     # Default: .pynext/build
```

### Minification

```python
# pynext.config.py

# Minify JavaScript and CSS
minify = True                   # Default: True in prod, False in dev

# Minification options
minify_options = {
    "js": True,
    "css": True,
    "html": True,
    "remove_comments": True,
    "collapse_whitespace": True
}
```

### Source Maps

```python
# pynext.config.py

# Generate source maps
source_maps = True              # Default: True in dev, False in prod

# Source map style
source_map_style = "inline"     # "inline", "external", "both"
```

### Asset Optimization

```python
# pynext.config.py

# Optimize assets during build
optimize_assets = True

# Image optimization
optimize_images = True
image_quality = 85              # JPEG/WebP quality (1-100)
image_formats = ["webp", "avif"] # Convert to modern formats

# CSS optimization
optimize_css = True
autoprefixer = True             # Add vendor prefixes
```

### Code Splitting

```python
# pynext.config.py

# Enable code splitting
code_splitting = True

# Split vendor code
vendor_splitting = True

# Chunk size limits (bytes)
chunk_size_limit = 50000        # 50KB
```

---

## Development Settings

### Hot Reload

```python
# pynext.config.py

# Enable hot reload
hot_reload = True               # Default: True in dev

# Directories to watch
watch_dirs = [
    "pages",
    "components",
    "static"
]

# Files to ignore
watch_ignore = [
    "*.pyc",
    "__pycache__",
    ".git",
    "node_modules"
]

# Debounce delay (ms)
watch_debounce = 100
```

### Browser Opening

```python
# pynext.config.py

# Open browser on server start
open_browser = True             # Default: False

# Browser to open
browser = "default"             # "default", "chrome", "firefox", "safari"
```

### Logging

```python
# pynext.config.py

# Log level
log_level = "DEBUG"             # DEBUG, INFO, WARNING, ERROR

# Log format
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Log file (optional)
log_file = "logs/pynext.log"

# Request logging
log_requests = True
log_request_body = False        # Be careful with sensitive data
```

### Error Display

```python
# pynext.config.py

# Show detailed errors
show_error_details = True       # Default: True in dev

# Error page customization
error_template = "errors/500.html"

# Include source code in errors
show_source_code = True
source_code_context_lines = 5
```

---

## Production Settings

### Recommended Production Config

```python
# pynext.config.py

import os

# Detect environment
ENV = os.getenv("PYNEXT_ENV", "development")
IS_PROD = ENV == "production"

# Server
host = "0.0.0.0" if IS_PROD else "localhost"
port = int(os.getenv("PORT", 3000))
debug = not IS_PROD
workers = os.cpu_count() * 2 + 1 if IS_PROD else 1

# Security
secret_key = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")

# Static files
static_cache_max_age = 31536000 if IS_PROD else 0

# Build
minify = IS_PROD
source_maps = not IS_PROD

# Logging
log_level = "INFO" if IS_PROD else "DEBUG"
show_error_details = not IS_PROD
```

### Security Settings

```python
# pynext.config.py

# CORS configuration
cors_enabled = True
cors_origins = [
    "https://example.com",
    "https://www.example.com"
]
cors_methods = ["GET", "POST", "PUT", "DELETE"]
cors_headers = ["Content-Type", "Authorization"]
cors_credentials = True

# CSRF protection
csrf_enabled = True
csrf_cookie_name = "csrf_token"
csrf_header_name = "X-CSRF-Token"

# Security headers
security_headers = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
}

# Trusted hosts
allowed_hosts = ["example.com", "www.example.com"]
```

### SSL/TLS

```python
# pynext.config.py

# SSL configuration (for direct SSL termination)
ssl_enabled = True
ssl_cert = "/path/to/cert.pem"
ssl_key = "/path/to/key.pem"

# Or use environment variables
import os
ssl_cert = os.getenv("SSL_CERT_PATH")
ssl_key = os.getenv("SSL_KEY_PATH")
```

---

## Environment Variables

### Loading Environment Variables

```python
# pynext.config.py

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Use environment variables
secret_key = os.getenv("SECRET_KEY")
database_url = os.getenv("DATABASE_URL")
debug = os.getenv("DEBUG", "false").lower() == "true"
```

### Environment-Specific Configs

```python
# pynext.config.py

import os

ENV = os.getenv("PYNEXT_ENV", "development")

# Base configuration
host = "localhost"
port = 3000
debug = True

# Override based on environment
if ENV == "production":
    host = "0.0.0.0"
    debug = False
    minify = True
    
elif ENV == "staging":
    host = "0.0.0.0"
    debug = True
    minify = True
    
elif ENV == "testing":
    port = 3001
    debug = True
```

### .env File Format

```bash
# .env

# Server
PYNEXT_ENV=development
PORT=3000
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://localhost/mydb

# External APIs
API_KEY=xxx
STRIPE_SECRET_KEY=sk_test_xxx

# Feature flags
ENABLE_NEW_FEATURE=true
```

### Environment Variable Precedence

1. System environment variables (highest)
2. `.env.local` (git-ignored)
3. `.env.{environment}` (e.g., `.env.production`)
4. `.env` (lowest)

```python
# Load order
from dotenv import load_dotenv
import os

env = os.getenv("PYNEXT_ENV", "development")

# Load in order (later overrides earlier)
load_dotenv(".env")
load_dotenv(f".env.{env}")
load_dotenv(".env.local")
```

---

## Advanced Configuration

### Custom Middleware

```python
# pynext.config.py

from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware

# Custom middleware stack
middleware = [
    Middleware(GZipMiddleware, minimum_size=1000),
    # Add your custom middleware here
]
```

### Custom Routes

```python
# pynext.config.py

# Additional routes (beyond file-based routing)
custom_routes = [
    {"path": "/health", "handler": "handlers.health_check"},
    {"path": "/metrics", "handler": "handlers.metrics"}
]

# API prefix
api_prefix = "/api/v1"
```

### Plugin System

```python
# pynext.config.py

# Plugins to load
plugins = [
    "pynext_auth",              # Authentication plugin
    "pynext_admin",             # Admin panel
    {"pynext_cache": {          # With configuration
        "backend": "redis",
        "url": "redis://localhost"
    }}
]
```

### Database Configuration

```python
# pynext.config.py

import os

# Database settings (for server actions)
database = {
    "url": os.getenv("DATABASE_URL", "sqlite:///./app.db"),
    "pool_size": 20,
    "max_overflow": 10,
    "pool_pre_ping": True
}

# Redis settings
redis = {
    "url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "db": 0
}
```

### Template Settings

```python
# pynext.config.py

# Page template customization
page_template = {
    "doctype": "<!DOCTYPE html>",
    "html_attrs": {"lang": "en"},
    "default_meta": [
        {"charset": "utf-8"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ],
    "default_head": [
        '<link rel="icon" href="/favicon.ico">'
    ]
}
```

---

## Complete Reference

### All Configuration Options

```python
# pynext.config.py - Complete Reference

import os

# =============================================================================
# ENVIRONMENT
# =============================================================================
ENV = os.getenv("PYNEXT_ENV", "development")
IS_PROD = ENV == "production"

# =============================================================================
# SERVER
# =============================================================================
host = "0.0.0.0" if IS_PROD else "localhost"
port = int(os.getenv("PORT", 3000))
debug = not IS_PROD
workers = (os.cpu_count() or 1) * 2 + 1 if IS_PROD else 1

# Timeouts
request_timeout = 30
keep_alive = 5
shutdown_timeout = 30

# =============================================================================
# ROUTING
# =============================================================================
pages_dir = "pages"
base_path = ""  # URL prefix for all routes

# =============================================================================
# NPM PACKAGES
# =============================================================================
npm_packages = [
    "chart.js",
    {"lodash": "^4.17.0"},
]

react_compat = False
bundle_dir = ".pynext/bundles"

esbuild_options = {
    "target": "es2020",
    "format": "esm",
    "minify": IS_PROD,
    "sourcemap": not IS_PROD,
}

# =============================================================================
# STATIC FILES
# =============================================================================
static_dir = "static"
static_url = "/static"
static_cache_max_age = 31536000 if IS_PROD else 0

# =============================================================================
# BUILD
# =============================================================================
build_dir = ".pynext/build"
minify = IS_PROD
source_maps = not IS_PROD
code_splitting = True

# =============================================================================
# DEVELOPMENT
# =============================================================================
hot_reload = not IS_PROD
open_browser = False
watch_dirs = ["pages", "components", "static"]
watch_ignore = ["*.pyc", "__pycache__", ".git", "node_modules"]

# =============================================================================
# LOGGING
# =============================================================================
log_level = "INFO" if IS_PROD else "DEBUG"
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
log_requests = True
show_error_details = not IS_PROD

# =============================================================================
# SECURITY
# =============================================================================
secret_key = os.getenv("SECRET_KEY", "change-me-in-production")

cors_enabled = True
cors_origins = ["*"] if not IS_PROD else [
    os.getenv("FRONTEND_URL", "https://example.com")
]

csrf_enabled = IS_PROD
allowed_hosts = ["*"] if not IS_PROD else [
    os.getenv("ALLOWED_HOST", "example.com")
]

# SSL (if not using reverse proxy)
ssl_enabled = False
ssl_cert = os.getenv("SSL_CERT_PATH")
ssl_key = os.getenv("SSL_KEY_PATH")
```

### Configuration Type Hints

For IDE support, you can use type hints:

```python
# pynext.config.py

from typing import List, Dict, Union, Optional

# Type hints for configuration
host: str = "localhost"
port: int = 3000
debug: bool = True
workers: int = 4

npm_packages: List[Union[str, Dict[str, str]]] = []

esbuild_options: Dict[str, Union[str, bool]] = {
    "target": "es2020",
    "minify": True
}

cors_origins: List[str] = ["*"]
```

### Validating Configuration

```python
# pynext.config.py

from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    host: str = "localhost"
    port: int = 3000
    debug: bool = True
    secret_key: str
    
    @validator("port")
    def port_must_be_valid(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @validator("secret_key")
    def secret_key_must_be_strong(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        return v
    
    class Config:
        env_file = ".env"

# Load and validate
settings = Settings()

# Export for pynext
host = settings.host
port = settings.port
debug = settings.debug
secret_key = settings.secret_key
```

---

## CLI Configuration Override

Configuration can be overridden via CLI:

```bash
# Override host and port
pynext dev --host 0.0.0.0 --port 8080

# Enable debug
pynext dev --debug

# Specify config file
pynext dev --config ./custom.config.py

# Set environment
PYNEXT_ENV=production pynext build
```

---

## Next Steps

- [Getting Started](GETTING_STARTED.md) - Project setup tutorial
- [Routing](ROUTING.md) - File-based routing system
- [Server Actions](SERVER_ACTIONS.md) - Server-side Python functions
- [State Management](STATE_MANAGEMENT.md) - Signals and reactivity

