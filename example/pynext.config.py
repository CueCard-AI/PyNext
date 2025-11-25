"""
PyNext Configuration for Example App
"""

# NPM packages to bundle
npm_packages = [
    # Add npm packages here for client-side use
    # "chart.js",
    # "lodash",
]

# Build options
build = {
    "output": ".pynext/build",
    "minify": True,
}

# Development options
dev = {
    "port": 3000,
    "host": "127.0.0.1",
}

