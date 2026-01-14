"""
PyNext Encoding API - Type Stubs for Text Encoding/Decoding

=============================================================================
WHO
=============================================================================

Developers who need to:
- Convert strings to binary data (Uint8Array)
- Decode binary data back to strings
- Encode/decode base64 data
- Handle different character encodings

=============================================================================
WHAT
=============================================================================

Python type stubs for the Web Encoding API:
- TextEncoder: Convert strings to UTF-8 bytes
- TextDecoder: Convert bytes to strings (multiple encodings)
- btoa: Encode binary string to base64
- atob: Decode base64 to binary string

=============================================================================
WHEN
=============================================================================

Use these APIs when you need to:
- Prepare string data for binary protocols (WebSocket, fetch)
- Read binary file contents as text
- Encode/decode base64 for data URLs or API payloads
- Handle text with specific encodings (UTF-8, ISO-8859-1)

=============================================================================
WHERE
=============================================================================

Client-side code decorated with @client that transpiles to JavaScript.
These are browser-native APIs available in all modern browsers.

=============================================================================
WHY
=============================================================================

- **Type Safety**: Full IDE autocompletion for all encoding APIs
- **Zero Runtime**: Direct passthrough to native browser APIs
- **Encoding Support**: Handle UTF-8, Latin-1, UTF-16, and more
- **AI-Friendly**: Comprehensive docstrings for LLM assistance

=============================================================================
HOW (Transpilation)
=============================================================================

All encoding APIs transpile directly to JavaScript without wrappers:

    Python:
        encoder = TextEncoder()
        bytes_data = encoder.encode("Hello, 世界!")
        
        decoder = TextDecoder("utf-8")
        text = decoder.decode(bytes_data)
    
    JavaScript (transpiled):
        let encoder = new TextEncoder();
        let bytes_data = encoder.encode("Hello, 世界!");
        
        let decoder = new TextDecoder("utf-8");
        let text = decoder.decode(bytes_data);

=============================================================================
"""

from typing import Optional, Union, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .binary import Uint8Array, ArrayBuffer


# =============================================================================
# TextEncoder Class
# =============================================================================

class TextEncoder:
    """
    Encode strings to UTF-8 byte sequences.
    
    WHO: Developers converting text to binary data
    WHAT: UTF-8 text encoding API
    WHEN: Preparing strings for binary protocols, file operations
    WHERE: Client-side transpiled code
    WHY: Type-safe text-to-bytes conversion
    HOW: Direct passthrough to native TextEncoder API
    
    Note: TextEncoder always uses UTF-8 encoding. This is by design
    in the Web API - UTF-8 is the universal encoding for the web.
    
    Example (Basic):
        encoder = TextEncoder()
        bytes_array = encoder.encode("Hello, World!")
        # bytes_array is Uint8Array with UTF-8 bytes
    
    Example (Unicode):
        encoder = TextEncoder()
        bytes_array = encoder.encode("Hello, 世界! 🌍")
        # Multi-byte sequences for non-ASCII characters
    
    Example (Encode into existing buffer):
        encoder = TextEncoder()
        buffer = Uint8Array(100)
        result = encoder.encodeInto("Hello", buffer)
        print(f"Read {result.read} chars, wrote {result.written} bytes")
    """
    
    def __init__(self) -> None:
        """
        Create a new TextEncoder.
        
        TextEncoder always uses UTF-8. No encoding parameter needed.
        
        Example:
            encoder = TextEncoder()
            encoder.encoding  # "utf-8"
        """
        ...
    
    @property
    def encoding(self) -> str:
        """
        The encoding used by this encoder. Always "utf-8".
        
        Example:
            encoder = TextEncoder()
            encoder.encoding  # "utf-8"
        """
        ...
    
    def encode(self, input: str = "") -> "Uint8Array":
        """
        Encode a string to a Uint8Array of UTF-8 bytes.
        
        Args:
            input: The string to encode. Defaults to empty string.
        
        Returns:
            Uint8Array containing the UTF-8 encoded bytes.
        
        Example:
            encoder = TextEncoder()
            
            # ASCII
            bytes_arr = encoder.encode("Hello")
            # [72, 101, 108, 108, 111]
            
            # Unicode
            bytes_arr = encoder.encode("世界")
            # [228, 184, 150, 231, 149, 140] (6 bytes for 2 chars)
            
            # Emoji
            bytes_arr = encoder.encode("🎉")
            # [240, 159, 142, 137] (4 bytes for 1 emoji)
        """
        ...
    
    def encodeInto(self, source: str, destination: "Uint8Array") -> Any:
        """
        Encode a string into an existing Uint8Array buffer.
        
        More efficient than encode() when you have a pre-allocated buffer,
        as it avoids creating a new Uint8Array.
        
        Args:
            source: The string to encode.
            destination: The Uint8Array to write bytes into.
        
        Returns:
            Object with:
            - read: Number of UTF-16 code units (characters) read from source
            - written: Number of bytes written to destination
        
        Example:
            encoder = TextEncoder()
            buffer = Uint8Array(100)
            
            result = encoder.encodeInto("Hello, World!", buffer)
            print(f"Read {result.read} chars")     # 13
            print(f"Wrote {result.written} bytes")  # 13
            
            # If buffer is too small:
            small_buffer = Uint8Array(5)
            result = encoder.encodeInto("Hello, World!", small_buffer)
            # result.read = 5, result.written = 5 (truncated)
        """
        ...


# =============================================================================
# TextDecoder Class
# =============================================================================

class TextDecoder:
    """
    Decode byte sequences to strings with multiple encoding support.
    
    WHO: Developers converting binary data to text
    WHAT: Text decoding API with encoding support
    WHEN: Reading binary file contents, receiving binary WebSocket messages
    WHERE: Client-side transpiled code
    WHY: Type-safe bytes-to-text conversion with encoding handling
    HOW: Direct passthrough to native TextDecoder API
    
    Supported Encodings:
        - "utf-8" (default, recommended)
        - "utf-16le", "utf-16be"
        - "iso-8859-1" (Latin-1)
        - "windows-1252"
        - And many more (see WHATWG Encoding Standard)
    
    Example (Basic UTF-8):
        decoder = TextDecoder()  # Default UTF-8
        text = decoder.decode(bytes_array)
    
    Example (Other Encodings):
        decoder = TextDecoder("iso-8859-1")
        text = decoder.decode(latin1_bytes)
    
    Example (Streaming):
        decoder = TextDecoder("utf-8")
        
        # Decode chunks, keeping state for incomplete sequences
        part1 = decoder.decode(chunk1, {"stream": True})
        part2 = decoder.decode(chunk2, {"stream": True})
        final = decoder.decode()  # Flush remaining
        
        full_text = part1 + part2 + final
    
    Example (Error Handling):
        # Throw on invalid byte sequences
        decoder = TextDecoder("utf-8", {"fatal": True})
        try:
            text = decoder.decode(invalid_bytes)
        except:
            console.error("Invalid UTF-8 sequence")
    """
    
    def __init__(
        self,
        label: str = "utf-8",
        options: Optional[dict] = None
    ) -> None:
        """
        Create a new TextDecoder.
        
        Args:
            label: The encoding to use. Common values:
                   - "utf-8" (default)
                   - "utf-16le", "utf-16be"
                   - "iso-8859-1" (Latin-1)
                   - "windows-1252"
            options: Optional configuration:
                     - fatal (bool): Throw on invalid sequences. Default False.
                     - ignoreBOM (bool): Ignore byte order mark. Default False.
        
        Raises:
            RangeError: If the encoding label is not recognized.
        
        Example:
            # Default UTF-8
            decoder = TextDecoder()
            
            # Latin-1 encoding
            decoder = TextDecoder("iso-8859-1")
            
            # UTF-8 with strict error handling
            decoder = TextDecoder("utf-8", {"fatal": True})
            
            # Ignore byte order mark
            decoder = TextDecoder("utf-8", {"ignoreBOM": True})
        """
        ...
    
    @property
    def encoding(self) -> str:
        """
        The encoding used by this decoder.
        
        Returns the canonical name of the encoding.
        
        Example:
            decoder = TextDecoder("UTF-8")
            decoder.encoding  # "utf-8" (normalized)
        """
        ...
    
    @property
    def fatal(self) -> bool:
        """
        Whether this decoder throws on invalid sequences.
        
        Example:
            decoder = TextDecoder("utf-8", {"fatal": True})
            decoder.fatal  # True
        """
        ...
    
    @property
    def ignoreBOM(self) -> bool:
        """
        Whether this decoder ignores the byte order mark.
        
        Example:
            decoder = TextDecoder("utf-8", {"ignoreBOM": True})
            decoder.ignoreBOM  # True
        """
        ...
    
    def decode(
        self,
        input: Optional[Union["ArrayBuffer", "Uint8Array", Any]] = None,
        options: Optional[dict] = None
    ) -> str:
        """
        Decode bytes to a string.
        
        Args:
            input: The bytes to decode. Can be:
                   - ArrayBuffer
                   - Uint8Array (or any TypedArray)
                   - DataView
                   - None (flush the decoder)
            options: Optional configuration:
                     - stream (bool): If True, don't flush the decoder.
                                      Use for streaming/chunked decoding.
        
        Returns:
            The decoded string.
        
        Raises:
            TypeError: If fatal=True and input contains invalid sequences.
        
        Example (Basic):
            decoder = TextDecoder()
            text = decoder.decode(bytes_array)
        
        Example (Streaming):
            decoder = TextDecoder()
            
            # Process chunks, keeping state for split multi-byte sequences
            result = ""
            for chunk in chunks:
                result += decoder.decode(chunk, {"stream": True})
            
            # Flush any remaining bytes
            result += decoder.decode()
        
        Example (Flush):
            # Call with no arguments to flush the decoder
            final = decoder.decode()
        """
        ...


# =============================================================================
# Base64 Functions
# =============================================================================

def btoa(data: str) -> str:
    """
    Encode a binary string to base64.
    
    WHO: Developers encoding binary data for text transport
    WHAT: Binary-to-ASCII base64 encoding
    WHEN: Creating data URLs, encoding for APIs, storing binary in JSON
    WHERE: Client-side transpiled code
    WHY: Convert binary data to ASCII-safe format
    HOW: Direct passthrough to native btoa function
    
    IMPORTANT: btoa only works with "binary strings" where each character
    is in the range 0-255 (Latin-1). For Unicode strings, encode to UTF-8 first.
    
    Args:
        data: A binary string (each char code 0-255).
    
    Returns:
        Base64 encoded string.
    
    Raises:
        InvalidCharacterError: If data contains characters outside 0-255.
    
    Example (ASCII):
        encoded = btoa("Hello, World!")
        # "SGVsbG8sIFdvcmxkIQ=="
    
    Example (Binary data):
        # Binary string (bytes as chars)
        binary = "".join(chr(b) for b in [0x89, 0x50, 0x4E, 0x47])
        encoded = btoa(binary)
    
    Example (Unicode - WRONG):
        btoa("Hello, 世界!")  # THROWS ERROR!
    
    Example (Unicode - CORRECT):
        # First encode to UTF-8, then convert to binary string
        encoder = TextEncoder()
        bytes_arr = encoder.encode("Hello, 世界!")
        binary = "".join(chr(b) for b in bytes_arr)
        encoded = btoa(binary)
    """
    ...


def atob(data: str) -> str:
    """
    Decode a base64 string to binary.
    
    WHO: Developers decoding base64 data
    WHAT: ASCII-to-binary base64 decoding
    WHEN: Reading data URLs, decoding API responses, reading stored binary
    WHERE: Client-side transpiled code
    WHY: Convert base64 back to binary data
    HOW: Direct passthrough to native atob function
    
    Args:
        data: A base64 encoded string.
    
    Returns:
        A binary string (each character is a byte 0-255).
    
    Raises:
        InvalidCharacterError: If data is not valid base64.
    
    Example (Basic):
        decoded = atob("SGVsbG8sIFdvcmxkIQ==")
        # "Hello, World!"
    
    Example (To Uint8Array):
        binary = atob(base64_string)
        bytes_arr = Uint8Array([ord(c) for c in binary])
    
    Example (Decode UTF-8):
        binary = atob(base64_string)
        bytes_arr = Uint8Array([ord(c) for c in binary])
        decoder = TextDecoder()
        text = decoder.decode(bytes_arr)
        # Now text can contain Unicode
    """
    ...


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "TextEncoder",
    "TextDecoder",
    "btoa",
    "atob",
]

