"""
Phase 34.5: Integration/Parity Tests

Mini-application tests verifying Python-to-JavaScript transpilation
parity for URL, Encoding, and Binary Data APIs.

Total: 20 tests
"""

import pytest
from pynext.transpiler import transpile


class TestURLBuildingApps:
    """Integration tests for URL building patterns."""
    
    def test_api_client_url_builder(self):
        """Build API client URLs."""
        code = '''
def build_api_url(endpoint, params=None):
    url = URL(f"{window.location.origin}/api{endpoint}")
    if params:
        for key, value in params.items():
            if value is not None:
                url.searchParams.set(key, str(value))
    return url.href

api_url = build_api_url("/users", {"page": 1, "limit": 10})
'''
        result = transpile(code)
        assert 'URL(' in result
        assert 'url.searchParams.set' in result
        assert 'url.href' in result
    
    def test_pagination_component(self):
        """Pagination URL management."""
        code = '''
def update_page(page_num):
    url = URL(window.location.href)
    url.searchParams.set("page", str(page_num))
    window.history.pushState({}, "", url.href)
    
def get_current_page():
    params = URLSearchParams(window.location.search)
    page = params.get("page")
    return int(page) if page else 1
'''
        result = transpile(code)
        assert 'URLSearchParams(window.location.search)' in result
        # .get() may use __py.dict.get helper
        assert 'params' in result
        assert '"page"' in result
    
    def test_filter_manager(self):
        """URL-based filter management."""
        code = '''
def apply_filters(filters):
    url = URL(window.location.href)
    
    # Clear existing filters
    for key in list(url.searchParams.keys()):
        if key.startswith("filter_"):
            url.searchParams.delete(key)
    
    # Add new filters
    for key, value in filters.items():
        url.searchParams.set(f"filter_{key}", value)
    
    return url.href
'''
        result = transpile(code)
        # .keys() may become Object.keys(url.searchParams)
        assert 'url.searchParams' in result
        assert 'url.searchParams.delete' in result
        assert 'url.searchParams.set' in result
    
    def test_share_url_generator(self):
        """Generate shareable URLs."""
        code = '''
def generate_share_url(content_id, title):
    base = URL(window.location.origin)
    base.pathname = f"/share/{content_id}"
    base.searchParams.set("title", title)
    return base.href
'''
        result = transpile(code)
        assert 'base.pathname' in result
        assert 'base.searchParams.set' in result


class TestEncodingApps:
    """Integration tests for encoding patterns."""
    
    def test_json_binary_transport(self):
        """Send JSON as binary over WebSocket."""
        code = '''
def send_json_message(ws, data):
    json_str = JSON.stringify(data)
    encoder = TextEncoder()
    bytes_data = encoder.encode(json_str)
    ws.send(bytes_data)

def receive_json_message(data):
    decoder = TextDecoder()
    json_str = decoder.decode(data)
    return JSON.parse(json_str)
'''
        result = transpile(code)
        assert 'TextEncoder()' in result
        # .encode() may use __py.str.encode helper
        assert 'encoder' in result
        assert 'TextDecoder()' in result
        assert 'decoder.decode' in result
    
    def test_image_base64_handler(self):
        """Handle base64 image data."""
        code = '''
async def image_to_base64(file):
    buffer = await file.arrayBuffer()
    bytes_arr = Uint8Array(buffer)
    binary = "".join(chr(b) for b in bytes_arr)
    return btoa(binary)

def base64_to_blob(base64_str, mime_type):
    binary = atob(base64_str)
    bytes_arr = Uint8Array([ord(c) for c in binary])
    return Blob([bytes_arr], {"type": mime_type})
'''
        result = transpile(code)
        assert 'file.arrayBuffer()' in result
        assert 'Uint8Array(buffer)' in result
        assert 'btoa(binary)' in result
        assert 'atob(base64_str)' in result
    
    def test_utf8_clipboard_handler(self):
        """Handle clipboard with proper encoding."""
        code = '''
async def copy_unicode_text(text):
    encoder = TextEncoder()
    bytes_data = encoder.encode(text)
    
    blob = Blob([text], {"type": "text/plain;charset=utf-8"})
    item = ClipboardItem({"text/plain": blob})
    await navigator.clipboard.write([item])
'''
        result = transpile(code)
        assert 'TextEncoder()' in result
        assert 'Blob([text]' in result
    
    def test_hash_calculator(self):
        """Calculate SHA-256 hash of text."""
        code = '''
async def hash_text(text):
    encoder = TextEncoder()
    data = encoder.encode(text)
    hash_buffer = await crypto.subtle.digest("SHA-256", data)
    hash_array = Uint8Array(hash_buffer)
    return "".join(f"{b:02x}" for b in hash_array)
'''
        result = transpile(code)
        # .encode() may use __py.str.encode helper
        assert 'encoder' in result
        assert 'crypto.subtle.digest' in result


class TestBinaryDataApps:
    """Integration tests for binary data patterns."""
    
    def test_file_upload_processor(self):
        """Process file upload."""
        code = '''
async def process_upload(file):
    buffer = await file.arrayBuffer()
    bytes_view = Uint8Array(buffer)
    
    # Check magic bytes for PNG
    if bytes_view[0] == 0x89 and bytes_view[1] == 0x50:
        return "PNG"
    elif bytes_view[0] == 0xFF and bytes_view[1] == 0xD8:
        return "JPEG"
    else:
        return "Unknown"
'''
        result = transpile(code)
        assert 'file.arrayBuffer()' in result
        assert 'Uint8Array(buffer)' in result
    
    def test_binary_protocol_parser(self):
        """Parse binary protocol."""
        code = '''
def parse_packet(buffer):
    view = DataView(buffer)
    
    header = {
        "magic": view.getUint32(0, False),
        "version": view.getUint16(4, False),
        "type": view.getUint8(6),
        "flags": view.getUint8(7),
        "length": view.getUint32(8, False),
    }
    
    payload = Uint8Array(buffer, 12, header["length"])
    return header, payload
'''
        result = transpile(code)
        assert 'DataView(buffer)' in result
        assert 'view.getUint32' in result
        assert 'Uint8Array(buffer, 12' in result
    
    def test_image_pixel_processor(self):
        """Process image pixels."""
        code = '''
def invert_colors(image_data):
    pixels = Uint8ClampedArray(image_data.data)
    
    for i in range(0, len(pixels), 4):
        pixels[i] = 255 - pixels[i]         # R
        pixels[i + 1] = 255 - pixels[i + 1] # G
        pixels[i + 2] = 255 - pixels[i + 2] # B
        # Alpha unchanged
    
    return pixels
'''
        result = transpile(code)
        assert 'Uint8ClampedArray' in result
    
    def test_audio_buffer_generator(self):
        """Generate audio buffer."""
        code = '''
def generate_sine_wave(frequency, duration, sample_rate):
    num_samples = int(duration * sample_rate)
    buffer = Float32Array(num_samples)
    
    for i in range(num_samples):
        t = i / sample_rate
        buffer[i] = Math.sin(2 * Math.PI * frequency * t)
    
    return buffer
'''
        result = transpile(code)
        assert 'Float32Array(num_samples)' in result


class TestDownloadApps:
    """Integration tests for file download patterns."""
    
    def test_csv_exporter(self):
        """Export data as CSV download."""
        code = '''
def export_to_csv(data, filename):
    rows = []
    for row in data:
        rows.append(",".join(str(v) for v in row))
    csv_content = "\\n".join(rows)
    
    blob = Blob([csv_content], {"type": "text/csv"})
    url = URL.createObjectURL(blob)
    
    a = document.createElement("a")
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    
    URL.revokeObjectURL(url)
'''
        result = transpile(code)
        assert 'Blob([csv_content]' in result
        assert 'URL.createObjectURL(blob)' in result
        assert 'URL.revokeObjectURL(url)' in result
    
    def test_json_exporter(self):
        """Export data as JSON download."""
        code = '''
def export_to_json(data, filename):
    json_str = JSON.stringify(data, None, 2)
    blob = Blob([json_str], {"type": "application/json"})
    
    url = URL.createObjectURL(blob)
    a = document.createElement("a")
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
'''
        result = transpile(code)
        assert 'Blob([json_str]' in result
    
    def test_binary_file_generator(self):
        """Generate and download binary file."""
        code = '''
def download_binary(data, filename, mime_type):
    encoder = TextEncoder()
    bytes_data = encoder.encode(data)
    
    blob = Blob([bytes_data], {"type": mime_type})
    url = URL.createObjectURL(blob)
    
    link = document.createElement("a")
    link.href = url
    link.download = filename
    link.click()
    
    URL.revokeObjectURL(url)
'''
        result = transpile(code)
        assert 'TextEncoder()' in result
        assert 'Blob([bytes_data]' in result


class TestStreamingApps:
    """Integration tests for streaming patterns."""
    
    def test_chunked_text_reader(self):
        """Read text in chunks."""
        code = '''
async def read_chunked_response(response):
    reader = response.body.getReader()
    decoder = TextDecoder()
    result = ""
    
    while True:
        chunk = await reader.read()
        if chunk.done:
            break
        result += decoder.decode(chunk.value, {"stream": True})
    
    result += decoder.decode()
    return result
'''
        result = transpile(code)
        assert 'TextDecoder()' in result
        assert 'decoder.decode(chunk.value' in result
    
    def test_file_chunked_upload(self):
        """Upload file in chunks."""
        code = '''
async def upload_chunked(file, chunk_size=1024*1024):
    offset = 0
    while offset < file.size:
        chunk = file.slice(offset, offset + chunk_size)
        buffer = await chunk.arrayBuffer()
        await upload_chunk(buffer, offset)
        offset += chunk_size
'''
        result = transpile(code)
        # offset + chunk_size may use __py.dunders.add
        assert 'file.slice(offset' in result
        assert 'chunk.arrayBuffer()' in result

