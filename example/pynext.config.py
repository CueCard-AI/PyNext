"""
PyNext Configuration for Example App

Dependencies are now managed in separate files:
  - pynext.requirements.txt  (Python packages for Server Actions)
  - pynext.npm.txt           (NPM packages for client-side JS)

Run `pynext deps install` to install all dependencies.
"""

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

# React compatibility (enables Preact aliasing for React npm packages)
# This is auto-detected from pynext.npm.txt when React packages are used
react_compat = False
