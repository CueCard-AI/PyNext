# PyNext URL, Encoding & Binary Data API

Complete guide to URL manipulation, text encoding/decoding, base64, and binary data handling in PyNext. Type-safe, zero-runtime APIs that transpile perfectly to JavaScript.

## Overview

### Who

- Frontend developers parsing and building URLs
- Developers handling binary file uploads/downloads
- Anyone working with text encoding, base64, or binary protocols

### What

PyNext provides full type stubs for Web Data APIs:
- **URL**: Parse, manipulate, and construct URLs
- **URLSearchParams**: Query string manipulation
- **TextEncoder/TextDecoder**: UTF-8 and other encodings
- **btoa/atob**: Base64 encoding/decoding
- **ArrayBuffer/TypedArrays**: Binary data handling
- **DataView**: Mixed-type binary access
- **Blob/File**: Immutable binary data with MIME types

### When

Use these APIs when you need to:
- Build API URLs with dynamic query parameters
- Parse current page URL and query strings
- Encode/decode text to binary for WebSocket or fetch
- Handle file uploads and create downloadable files
- Work with binary protocols or image pixel data

### Where

Client-side code decorated with `@client` that transpiles to JavaScript.
These are browser-native APIs available in all modern browsers.

### Why

- **Type Safety**: Full IDE autocompletion for all APIs
- **Zero Runtime**: Direct passthrough transpilation - no overhead
- **AI-Friendly**: Comprehensive docstrings for LLM assistance
- **Pythonic**: Familiar Python syntax for JavaScript APIs

### How (Transpilation)

All APIs transpile directly to JavaScript without wrappers:

```python
# Python
url = URL("https://example.com?page=1")
url.searchParams.set("page", "2")

encoder = TextEncoder()
bytes_data = encoder.encode("Hello")
```

```javascript
// JavaScript (transpiled)
let url = new URL("https://example.com?page=1");
url.searchParams.set("page", "2");

let encoder = new TextEncoder();
let bytes_data = encoder.encode("Hello");
```

---

## URL API

### URL Class

Parse and manipulate URLs with full access to all components.

```python
from pynext.client import URL

# Construct from string
url = URL("https://user:pass@example.com:8080/path?foo=bar#section")

# Access components
url.href          # "https://user:pass@example.com:8080/path?foo=bar#section"
url.protocol      # "https:"
url.username      # "user"
url.password      # "pass"
url.host          # "example.com:8080"
url.hostname      # "example.com"
url.port          # "8080"
url.pathname      # "/path"
url.search        # "?foo=bar"
url.hash          # "#section"
url.origin        # "https://example.com:8080" (read-only)
url.searchParams  # URLSearchParams object (read-only)

# Modify components
url.pathname = "/new/path"
url.hash = "#new-section"

# Convert to string
str(url)          # Full URL string
url.toString()    # Same as str()
url.toJSON()      # Same (for JSON.stringify)
```

### Relative URL Resolution

```python
base = URL("https://example.com/a/b/c")
relative = URL("../d", base)
relative.href  # "https://example.com/a/d"

# Resolve from current page
current = URL("/api/users", window.location.origin)
```

### Static Methods

```python
# Create blob URL for downloads
blob = Blob([data], {"type": "text/csv"})
url = URL.createObjectURL(blob)

# Clean up when done
URL.revokeObjectURL(url)
```

---

## URLSearchParams

Utility class for query string manipulation.

```python
from pynext.client import URLSearchParams

# Create from string
params = URLSearchParams("foo=1&bar=2&foo=3")

# Create from dict
params = URLSearchParams({"page": "1", "limit": "10"})

# Create from tuples (allows duplicates)
params = URLSearchParams([("tag", "python"), ("tag", "web")])

# Read values
params.get("foo")       # "1" (first value)
params.getAll("foo")    # ["1", "3"] (all values)
params.has("bar")       # True

# Modify values
params.set("foo", "new")      # Replace all values
params.append("foo", "extra") # Add new value
params.delete("foo")          # Delete all values
params.delete("foo", "1")     # Delete specific value

# Sort alphabetically
params.sort()

# Iterate
for key in params.keys():
    print(key)

for value in params.values():
    print(value)

for key, value in params.entries():
    print(f"{key}={value}")

# Convert to string
params.toString()  # "foo=1&bar=2" (no leading ?)
```

### Common URL Patterns

```python
# Build API URL
@client
def build_api_url(endpoint, **params):
    url = URL(f"{window.location.origin}/api{endpoint}")
    for key, value in params.items():
        if value is not None:
            url.searchParams.set(key, str(value))
    return url.href

api_url = build_api_url("/users", page=1, limit=10)

# Parse current URL params
@client
def get_query_param(name, default=None):
    params = URLSearchParams(window.location.search)
    return params.get(name) or default

# Update URL without reload
@client
def update_query_param(name, value):
    url = URL(window.location.href)
    url.searchParams.set(name, value)
    window.history.pushState({}, "", url.href)
```

---

## Text Encoding

### TextEncoder

Convert strings to UTF-8 bytes.

```python
from pynext.client import TextEncoder

encoder = TextEncoder()
encoder.encoding  # "utf-8" (always)

# Encode string to Uint8Array
bytes_arr = encoder.encode("Hello, 世界!")

# Encode into existing buffer (more efficient)
buffer = Uint8Array(100)
result = encoder.encodeInto("Hello", buffer)
print(f"Read {result.read} chars, wrote {result.written} bytes")
```

### TextDecoder

Convert bytes to strings with multiple encoding support.

```python
from pynext.client import TextDecoder

# Default UTF-8
decoder = TextDecoder()

# Other encodings
decoder = TextDecoder("iso-8859-1")  # Latin-1
decoder = TextDecoder("utf-16le")    # UTF-16

# With options
decoder = TextDecoder("utf-8", {
    "fatal": True,      # Throw on invalid sequences
    "ignoreBOM": True,  # Ignore byte order mark
})

# Decode bytes to string
text = decoder.decode(bytes_array)

# Streaming decode (for chunked data)
decoder = TextDecoder()
result = ""
for chunk in chunks:
    result += decoder.decode(chunk, {"stream": True})
result += decoder.decode()  # Flush remaining
```

---

## Base64 Encoding

### btoa (Binary to ASCII)

```python
from pynext.client import btoa, atob

# Encode ASCII string
encoded = btoa("Hello, World!")  # "SGVsbG8sIFdvcmxkIQ=="

# For Unicode, encode to UTF-8 first
@client
def unicode_to_base64(text):
    encoder = TextEncoder()
    bytes_arr = encoder.encode(text)
    binary = "".join(chr(b) for b in bytes_arr)
    return btoa(binary)
```

### atob (ASCII to Binary)

```python
# Decode base64
decoded = atob("SGVsbG8sIFdvcmxkIQ==")  # "Hello, World!"

# Convert to bytes
@client
def base64_to_bytes(base64_str):
    binary = atob(base64_str)
    return Uint8Array([ord(c) for c in binary])

# Decode as Unicode
@client
def base64_to_unicode(base64_str):
    bytes_arr = base64_to_bytes(base64_str)
    decoder = TextDecoder()
    return decoder.decode(bytes_arr)
```

---

## Binary Data

### ArrayBuffer

Raw binary data container.

```python
from pynext.client import ArrayBuffer

buffer = ArrayBuffer(256)  # 256 bytes of zeros
buffer.byteLength          # 256

# Slice (creates copy)
first_half = buffer.slice(0, 128)
last_10 = buffer.slice(-10)

# Check if value is a view
ArrayBuffer.isView(Uint8Array(10))  # True
```

### Typed Arrays

```python
from pynext.client import (
    Uint8Array, Int8Array, Uint8ClampedArray,
    Int16Array, Uint16Array,
    Int32Array, Uint32Array,
    Float32Array, Float64Array,
    BigInt64Array, BigUint64Array,
)

# Create from length
arr = Uint8Array(10)  # 10 zeros

# Create from values
arr = Uint8Array([1, 2, 3, 4, 5])

# Create from ArrayBuffer
buffer = ArrayBuffer(100)
arr = Uint8Array(buffer)
arr = Uint8Array(buffer, 10, 20)  # offset 10, length 20

# Properties
arr.length        # Number of elements
arr.byteLength    # Size in bytes
arr.byteOffset    # Offset in buffer
arr.buffer        # Underlying ArrayBuffer
Uint8Array.BYTES_PER_ELEMENT  # 1

# Methods
arr.set([1, 2, 3], 0)     # Copy values
sub = arr.subarray(2, 5)  # View (no copy)
copy = arr.slice(0, 5)    # Copy
arr.fill(255)             # Fill with value
arr.indexOf(3)            # Find index
arr.includes(5)           # Check contains
```

### DataView

Read/write mixed types with explicit endianness.

```python
from pynext.client import DataView

buffer = ArrayBuffer(16)
view = DataView(buffer)

# Write values
view.setInt32(0, 12345, True)    # Little-endian
view.setFloat32(4, 3.14159, True)
view.setUint16(8, 65535, False)  # Big-endian

# Read values
int_val = view.getInt32(0, True)
float_val = view.getFloat32(4, True)

# All methods:
# getInt8, setInt8, getUint8, setUint8
# getInt16, setInt16, getUint16, setUint16
# getInt32, setInt32, getUint32, setUint32
# getFloat32, setFloat32, getFloat64, setFloat64
# getBigInt64, setBigInt64, getBigUint64, setBigUint64
```

---

## Blob and File

### Blob

Immutable binary data with MIME type.

```python
from pynext.client import Blob

# Create from string
blob = Blob(["Hello, World!"], {"type": "text/plain"})

# Create from bytes
data = Uint8Array([0x89, 0x50, 0x4E, 0x47])
blob = Blob([data], {"type": "image/png"})

# Properties
blob.size  # Size in bytes
blob.type  # MIME type

# Methods
sliced = blob.slice(0, 5)           # Slice
text = await blob.text()            # Read as text
buffer = await blob.arrayBuffer()   # Read as ArrayBuffer
```

### File Download Pattern

```python
@client
def download_csv(data, filename):
    # Create CSV content
    rows = ["name,email,age"]
    for person in data:
        rows.append(f"{person['name']},{person['email']},{person['age']}")
    csv_content = "\n".join(rows)
    
    # Create blob and download
    blob = Blob([csv_content], {"type": "text/csv"})
    url = URL.createObjectURL(blob)
    
    a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    
    URL.revokeObjectURL(url)
```

---

## Common Patterns

### JSON over WebSocket

```python
@client
def send_json(ws, data):
    json_str = JSON.stringify(data)
    encoder = TextEncoder()
    ws.send(encoder.encode(json_str))

@client
def receive_json(data):
    decoder = TextDecoder()
    json_str = decoder.decode(data)
    return JSON.parse(json_str)
```

### Image to Base64

```python
@client
async def image_to_base64(file):
    buffer = await file.arrayBuffer()
    bytes_arr = Uint8Array(buffer)
    binary = "".join(chr(b) for b in bytes_arr)
    return f"data:{file.type};base64,{btoa(binary)}"
```

### Parse Binary Protocol

```python
@client
def parse_header(buffer):
    view = DataView(buffer)
    return {
        "magic": view.getUint32(0, False),
        "version": view.getUint16(4, False),
        "type": view.getUint8(6),
        "length": view.getUint32(8, False),
    }
```

---

## Browser Compatibility

All APIs are native browser features with excellent support:

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| URL | ✅ | ✅ | ✅ | ✅ |
| URLSearchParams | ✅ | ✅ | ✅ | ✅ |
| TextEncoder | ✅ | ✅ | ✅ | ✅ |
| TextDecoder | ✅ | ✅ | ✅ | ✅ |
| btoa/atob | ✅ | ✅ | ✅ | ✅ |
| ArrayBuffer | ✅ | ✅ | ✅ | ✅ |
| TypedArrays | ✅ | ✅ | ✅ | ✅ |
| DataView | ✅ | ✅ | ✅ | ✅ |
| Blob | ✅ | ✅ | ✅ | ✅ |

---

## See Also

- [DOM API](./DOM_API.md) - Element and document manipulation
- [Events](./EVENTS.md) - Event handling
- [CSS Styling](./CSS_STYLING.md) - Style manipulation

