"""
PyNext Binary API - Type Stubs for ArrayBuffer, TypedArrays, DataView, Blob

=============================================================================
WHO
=============================================================================

Developers who need to:
- Work with raw binary data
- Handle file uploads and downloads
- Process images, audio, and other binary formats
- Interface with low-level APIs (WebGL, WebAudio, WebSocket)

=============================================================================
WHAT
=============================================================================

Python type stubs for the Web Binary Data APIs:
- ArrayBuffer: Raw binary data container
- TypedArrays: Uint8Array, Int32Array, Float64Array, etc.
- DataView: Mixed-type binary data access
- Blob: Immutable binary data with MIME type

=============================================================================
WHEN
=============================================================================

Use these APIs when you need to:
- Read/write binary files
- Process image pixel data (Canvas ImageData)
- Send/receive binary WebSocket messages
- Create downloadable files from generated data

=============================================================================
WHERE
=============================================================================

Client-side code decorated with @client that transpiles to JavaScript.
These are browser-native APIs available in all modern browsers.

=============================================================================
WHY
=============================================================================

- **Type Safety**: Full IDE autocompletion for all binary APIs
- **Zero Runtime**: Direct passthrough to native browser APIs
- **Performance**: Efficient binary data handling
- **AI-Friendly**: Comprehensive docstrings for LLM assistance

=============================================================================
HOW (Transpilation)
=============================================================================

All binary APIs transpile directly to JavaScript without wrappers:

    Python:
        buffer = ArrayBuffer(256)
        view = Uint8Array(buffer)
        view[0] = 255
    
    JavaScript (transpiled):
        let buffer = new ArrayBuffer(256);
        let view = new Uint8Array(buffer);
        view[0] = 255;

=============================================================================
"""

from typing import Optional, Union, Iterator, Any, List


# =============================================================================
# ArrayBuffer Class
# =============================================================================

class ArrayBuffer:
    """
    Raw binary data buffer of fixed size.
    
    WHO: Developers working with raw binary data
    WHAT: Fixed-length container for binary data
    WHEN: Low-level data processing, WebGL, file handling
    WHERE: Client-side transpiled code
    WHY: Foundation for all typed array operations
    HOW: Direct passthrough to native ArrayBuffer API
    
    ArrayBuffer cannot be read or written directly - use TypedArrays
    or DataView to access the data.
    
    Example:
        buffer = ArrayBuffer(256)  # 256 bytes
        
        # Access via TypedArray
        bytes_view = Uint8Array(buffer)
        bytes_view[0] = 42
        
        # Access via DataView
        data_view = DataView(buffer)
        data_view.setInt32(0, 12345)
    """
    
    def __init__(self, length: int) -> None:
        """
        Create a new ArrayBuffer with the specified size.
        
        The buffer is initialized to all zeros.
        
        Args:
            length: Size in bytes.
        
        Example:
            buffer = ArrayBuffer(1024)  # 1KB buffer
            buffer.byteLength  # 1024
        """
        ...
    
    @property
    def byteLength(self) -> int:
        """
        The size of the buffer in bytes. Read-only.
        
        Example:
            buffer = ArrayBuffer(100)
            buffer.byteLength  # 100
        """
        ...
    
    def slice(self, begin: int = 0, end: Optional[int] = None) -> "ArrayBuffer":
        """
        Create a copy of a portion of this buffer.
        
        Args:
            begin: Start index (inclusive). Negative counts from end.
            end: End index (exclusive). Defaults to buffer length.
        
        Returns:
            A new ArrayBuffer containing the copied bytes.
        
        Example:
            buffer = ArrayBuffer(100)
            first_half = buffer.slice(0, 50)
            last_10 = buffer.slice(-10)
        """
        ...
    
    @staticmethod
    def isView(arg: Any) -> bool:
        """
        Check if the argument is a view of an ArrayBuffer.
        
        Returns True for TypedArrays and DataView.
        
        Example:
            ArrayBuffer.isView(Uint8Array(10))  # True
            ArrayBuffer.isView(DataView(ArrayBuffer(10)))  # True
            ArrayBuffer.isView(ArrayBuffer(10))  # False
        """
        ...


# =============================================================================
# Base TypedArray (shared functionality)
# =============================================================================

class _TypedArrayBase:
    """
    Base class for all typed arrays (not directly usable).
    
    All typed arrays share these properties and methods.
    """
    
    @property
    def buffer(self) -> ArrayBuffer:
        """The underlying ArrayBuffer."""
        ...
    
    @property
    def byteLength(self) -> int:
        """The length of the array in bytes."""
        ...
    
    @property
    def byteOffset(self) -> int:
        """The offset in bytes from the start of the buffer."""
        ...
    
    @property
    def length(self) -> int:
        """The number of elements in the array."""
        ...
    
    BYTES_PER_ELEMENT: int
    """Number of bytes per element (class property)."""
    
    def __getitem__(self, index: int) -> Any:
        """Get element at index."""
        ...
    
    def __setitem__(self, index: int, value: Any) -> None:
        """Set element at index."""
        ...
    
    def __len__(self) -> int:
        """Return the number of elements."""
        ...
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate over elements."""
        ...
    
    def set(self, array: Union[list, "_TypedArrayBase"], offset: int = 0) -> None:
        """
        Copy values from an array into this typed array.
        
        Args:
            array: Source array (list or typed array).
            offset: Position to start writing at.
        
        Example:
            arr = Uint8Array(10)
            arr.set([1, 2, 3], 0)
            arr.set([7, 8, 9], 7)
        """
        ...
    
    def subarray(self, begin: int = 0, end: Optional[int] = None) -> "_TypedArrayBase":
        """
        Return a new view of the same buffer (no copy).
        
        Args:
            begin: Start index (inclusive).
            end: End index (exclusive).
        
        Returns:
            A new typed array sharing the same buffer.
        """
        ...
    
    def slice(self, begin: int = 0, end: Optional[int] = None) -> "_TypedArrayBase":
        """
        Create a copy of a portion of this array.
        
        Args:
            begin: Start index (inclusive).
            end: End index (exclusive).
        
        Returns:
            A new typed array with copied data.
        """
        ...
    
    def fill(self, value: Any, start: int = 0, end: Optional[int] = None) -> "_TypedArrayBase":
        """Fill the array with a value."""
        ...
    
    def copyWithin(self, target: int, start: int, end: Optional[int] = None) -> "_TypedArrayBase":
        """Copy a sequence of elements within the array."""
        ...
    
    def reverse(self) -> "_TypedArrayBase":
        """Reverse the array in place."""
        ...
    
    def sort(self, compareFn: Optional[Any] = None) -> "_TypedArrayBase":
        """Sort the array in place."""
        ...
    
    def indexOf(self, searchElement: Any, fromIndex: int = 0) -> int:
        """Find the first index of an element."""
        ...
    
    def lastIndexOf(self, searchElement: Any, fromIndex: Optional[int] = None) -> int:
        """Find the last index of an element."""
        ...
    
    def includes(self, searchElement: Any, fromIndex: int = 0) -> bool:
        """Check if the array includes an element."""
        ...
    
    def find(self, predicate: Any, thisArg: Any = None) -> Any:
        """Find the first element matching a predicate."""
        ...
    
    def findIndex(self, predicate: Any, thisArg: Any = None) -> int:
        """Find the index of the first element matching a predicate."""
        ...
    
    def every(self, predicate: Any, thisArg: Any = None) -> bool:
        """Test if all elements pass a predicate."""
        ...
    
    def some(self, predicate: Any, thisArg: Any = None) -> bool:
        """Test if any element passes a predicate."""
        ...
    
    def filter(self, predicate: Any, thisArg: Any = None) -> "_TypedArrayBase":
        """Create a new array with elements passing a predicate."""
        ...
    
    def map(self, callback: Any, thisArg: Any = None) -> "_TypedArrayBase":
        """Create a new array with results of calling a function on each element."""
        ...
    
    def reduce(self, callback: Any, initialValue: Any = None) -> Any:
        """Reduce the array to a single value (left to right)."""
        ...
    
    def reduceRight(self, callback: Any, initialValue: Any = None) -> Any:
        """Reduce the array to a single value (right to left)."""
        ...
    
    def forEach(self, callback: Any, thisArg: Any = None) -> None:
        """Execute a function for each element."""
        ...
    
    def join(self, separator: str = ",") -> str:
        """Join all elements into a string."""
        ...
    
    def keys(self) -> Iterator[int]:
        """Return an iterator over indices."""
        ...
    
    def values(self) -> Iterator[Any]:
        """Return an iterator over values."""
        ...
    
    def entries(self) -> Iterator[tuple]:
        """Return an iterator over [index, value] pairs."""
        ...


# =============================================================================
# Uint8Array
# =============================================================================

class Uint8Array(_TypedArrayBase):
    """
    8-bit unsigned integer array (0-255 per element).
    
    The most commonly used typed array for binary data.
    
    Example:
        # From length
        arr = Uint8Array(10)  # 10 zeros
        
        # From values
        arr = Uint8Array([72, 101, 108, 108, 111])  # "Hello" bytes
        
        # From ArrayBuffer
        buffer = ArrayBuffer(100)
        arr = Uint8Array(buffer)
        
        # From portion of ArrayBuffer
        arr = Uint8Array(buffer, 10, 20)  # offset 10, length 20
    """
    
    BYTES_PER_ELEMENT: int = 1
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None:
        """
        Create a new Uint8Array.
        
        Args:
            source: One of:
                    - int: Create array of this length (zeros)
                    - list: Create from values
                    - ArrayBuffer: Create view of buffer
                    - TypedArray: Copy from another typed array
            byteOffset: Offset in buffer (only for ArrayBuffer source).
            length: Length in elements (only for ArrayBuffer source).
        """
        ...
    
    def subarray(self, begin: int = 0, end: Optional[int] = None) -> "Uint8Array":
        """Return a new Uint8Array view of the same buffer."""
        ...
    
    def slice(self, begin: int = 0, end: Optional[int] = None) -> "Uint8Array":
        """Create a copy of a portion of this array."""
        ...


class Int8Array(_TypedArrayBase):
    """8-bit signed integer array (-128 to 127)."""
    BYTES_PER_ELEMENT: int = 1
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class Uint8ClampedArray(_TypedArrayBase):
    """
    8-bit unsigned integer array with clamping (0-255).
    
    Values outside 0-255 are clamped, not wrapped.
    Used for Canvas ImageData.
    """
    BYTES_PER_ELEMENT: int = 1
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class Int16Array(_TypedArrayBase):
    """16-bit signed integer array (-32768 to 32767)."""
    BYTES_PER_ELEMENT: int = 2
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class Uint16Array(_TypedArrayBase):
    """16-bit unsigned integer array (0 to 65535)."""
    BYTES_PER_ELEMENT: int = 2
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class Int32Array(_TypedArrayBase):
    """32-bit signed integer array."""
    BYTES_PER_ELEMENT: int = 4
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class Uint32Array(_TypedArrayBase):
    """32-bit unsigned integer array."""
    BYTES_PER_ELEMENT: int = 4
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class Float32Array(_TypedArrayBase):
    """32-bit floating point array (single precision)."""
    BYTES_PER_ELEMENT: int = 4
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class Float64Array(_TypedArrayBase):
    """64-bit floating point array (double precision)."""
    BYTES_PER_ELEMENT: int = 8
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class BigInt64Array(_TypedArrayBase):
    """64-bit signed BigInt array."""
    BYTES_PER_ELEMENT: int = 8
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


class BigUint64Array(_TypedArrayBase):
    """64-bit unsigned BigInt array."""
    BYTES_PER_ELEMENT: int = 8
    
    def __init__(
        self,
        source: Optional[Union[int, list, ArrayBuffer, "_TypedArrayBase"]] = None,
        byteOffset: int = 0,
        length: Optional[int] = None
    ) -> None: ...


# =============================================================================
# DataView Class
# =============================================================================

class DataView:
    """
    View for reading/writing mixed types from an ArrayBuffer.
    
    Unlike TypedArrays, DataView allows reading different types
    at different offsets and explicit endianness control.
    
    Example:
        buffer = ArrayBuffer(16)
        view = DataView(buffer)
        
        # Write a 32-bit int at offset 0 (little-endian)
        view.setInt32(0, 12345, True)
        
        # Write a float at offset 4
        view.setFloat32(4, 3.14159, True)
        
        # Read back
        int_val = view.getInt32(0, True)
        float_val = view.getFloat32(4, True)
    """
    
    def __init__(
        self,
        buffer: ArrayBuffer,
        byteOffset: int = 0,
        byteLength: Optional[int] = None
    ) -> None:
        """
        Create a DataView for an ArrayBuffer.
        
        Args:
            buffer: The underlying ArrayBuffer.
            byteOffset: Offset in bytes from buffer start.
            byteLength: Length in bytes (defaults to remainder of buffer).
        """
        ...
    
    @property
    def buffer(self) -> ArrayBuffer:
        """The underlying ArrayBuffer."""
        ...
    
    @property
    def byteLength(self) -> int:
        """The length of this view in bytes."""
        ...
    
    @property
    def byteOffset(self) -> int:
        """The offset from buffer start in bytes."""
        ...
    
    # =========================================================================
    # 8-bit methods (no endianness needed)
    # =========================================================================
    
    def getInt8(self, byteOffset: int) -> int:
        """Read a signed 8-bit integer."""
        ...
    
    def setInt8(self, byteOffset: int, value: int) -> None:
        """Write a signed 8-bit integer."""
        ...
    
    def getUint8(self, byteOffset: int) -> int:
        """Read an unsigned 8-bit integer."""
        ...
    
    def setUint8(self, byteOffset: int, value: int) -> None:
        """Write an unsigned 8-bit integer."""
        ...
    
    # =========================================================================
    # 16-bit methods
    # =========================================================================
    
    def getInt16(self, byteOffset: int, littleEndian: bool = False) -> int:
        """Read a signed 16-bit integer."""
        ...
    
    def setInt16(self, byteOffset: int, value: int, littleEndian: bool = False) -> None:
        """Write a signed 16-bit integer."""
        ...
    
    def getUint16(self, byteOffset: int, littleEndian: bool = False) -> int:
        """Read an unsigned 16-bit integer."""
        ...
    
    def setUint16(self, byteOffset: int, value: int, littleEndian: bool = False) -> None:
        """Write an unsigned 16-bit integer."""
        ...
    
    # =========================================================================
    # 32-bit methods
    # =========================================================================
    
    def getInt32(self, byteOffset: int, littleEndian: bool = False) -> int:
        """Read a signed 32-bit integer."""
        ...
    
    def setInt32(self, byteOffset: int, value: int, littleEndian: bool = False) -> None:
        """Write a signed 32-bit integer."""
        ...
    
    def getUint32(self, byteOffset: int, littleEndian: bool = False) -> int:
        """Read an unsigned 32-bit integer."""
        ...
    
    def setUint32(self, byteOffset: int, value: int, littleEndian: bool = False) -> None:
        """Write an unsigned 32-bit integer."""
        ...
    
    def getFloat32(self, byteOffset: int, littleEndian: bool = False) -> float:
        """Read a 32-bit float."""
        ...
    
    def setFloat32(self, byteOffset: int, value: float, littleEndian: bool = False) -> None:
        """Write a 32-bit float."""
        ...
    
    # =========================================================================
    # 64-bit methods
    # =========================================================================
    
    def getFloat64(self, byteOffset: int, littleEndian: bool = False) -> float:
        """Read a 64-bit float (double)."""
        ...
    
    def setFloat64(self, byteOffset: int, value: float, littleEndian: bool = False) -> None:
        """Write a 64-bit float (double)."""
        ...
    
    def getBigInt64(self, byteOffset: int, littleEndian: bool = False) -> int:
        """Read a signed 64-bit BigInt."""
        ...
    
    def setBigInt64(self, byteOffset: int, value: int, littleEndian: bool = False) -> None:
        """Write a signed 64-bit BigInt."""
        ...
    
    def getBigUint64(self, byteOffset: int, littleEndian: bool = False) -> int:
        """Read an unsigned 64-bit BigInt."""
        ...
    
    def setBigUint64(self, byteOffset: int, value: int, littleEndian: bool = False) -> None:
        """Write an unsigned 64-bit BigInt."""
        ...


# =============================================================================
# Blob Class
# =============================================================================

class Blob:
    """
    Immutable raw binary data with optional MIME type.
    
    Used for:
    - File downloads
    - Uploading to APIs
    - Creating object URLs
    - Reading file contents
    
    Example (Create from string):
        blob = Blob(["Hello, World!"], {"type": "text/plain"})
    
    Example (Create from bytes):
        data = Uint8Array([0x89, 0x50, 0x4E, 0x47])
        blob = Blob([data], {"type": "image/png"})
    
    Example (Create download):
        blob = Blob([csv_content], {"type": "text/csv"})
        url = URL.createObjectURL(blob)
        
        a = document.createElement("a")
        a.href = url
        a.download = "data.csv"
        a.click()
        
        URL.revokeObjectURL(url)
    
    Example (Read as text):
        async def read_blob(blob):
            text = await blob.text()
            return text
    """
    
    def __init__(
        self,
        blobParts: Optional[List[Union[str, "Blob", ArrayBuffer, "_TypedArrayBase"]]] = None,
        options: Optional[dict] = None
    ) -> None:
        """
        Create a new Blob.
        
        Args:
            blobParts: Array of data parts. Each can be:
                       - String
                       - Blob (concatenated)
                       - ArrayBuffer
                       - TypedArray
            options: Optional configuration:
                     - type (str): MIME type (e.g., "text/plain")
                     - endings (str): "transparent" or "native" for line endings
        
        Example:
            # Text blob
            blob = Blob(["Hello, World!"], {"type": "text/plain"})
            
            # Binary blob
            blob = Blob([bytes_array], {"type": "application/octet-stream"})
            
            # Combined
            blob = Blob([header_bytes, body_string, footer_blob])
        """
        ...
    
    @property
    def size(self) -> int:
        """
        The size of the blob in bytes.
        
        Example:
            blob = Blob(["Hello"])
            blob.size  # 5
        """
        ...
    
    @property
    def type(self) -> str:
        """
        The MIME type of the blob.
        
        Empty string if not specified.
        
        Example:
            blob = Blob(["data"], {"type": "text/csv"})
            blob.type  # "text/csv"
        """
        ...
    
    def slice(
        self,
        start: int = 0,
        end: Optional[int] = None,
        contentType: str = ""
    ) -> "Blob":
        """
        Create a new Blob with a subset of this blob's data.
        
        Args:
            start: Start byte (inclusive).
            end: End byte (exclusive).
            contentType: MIME type for the new blob.
        
        Returns:
            A new Blob with the sliced data.
        
        Example:
            blob = Blob(["Hello, World!"])
            first_five = blob.slice(0, 5)
        """
        ...
    
    def text(self) -> Any:
        """
        Read the blob contents as UTF-8 text.
        
        Returns a Promise that resolves to a string.
        
        Example:
            text = await blob.text()
        """
        ...
    
    def arrayBuffer(self) -> Any:
        """
        Read the blob contents as an ArrayBuffer.
        
        Returns a Promise that resolves to an ArrayBuffer.
        
        Example:
            buffer = await blob.arrayBuffer()
            bytes_view = Uint8Array(buffer)
        """
        ...
    
    def stream(self) -> Any:
        """
        Return a ReadableStream for reading the blob.
        
        Example:
            stream = blob.stream()
            reader = stream.getReader()
        """
        ...


# =============================================================================
# File Class (extends Blob)
# =============================================================================

class File(Blob):
    """
    A Blob with filename and modification time.
    
    Typically obtained from <input type="file"> or drag-and-drop.
    
    Example (from input):
        def on_change(event):
            file = event.target.files[0]
            console.log(f"Name: {file.name}")
            console.log(f"Size: {file.size}")
            console.log(f"Type: {file.type}")
            console.log(f"Modified: {file.lastModified}")
    
    Example (create programmatically):
        file = File(
            ["Hello, World!"],
            "hello.txt",
            {"type": "text/plain", "lastModified": Date.now()}
        )
    """
    
    def __init__(
        self,
        fileBits: List[Union[str, Blob, ArrayBuffer, "_TypedArrayBase"]],
        fileName: str,
        options: Optional[dict] = None
    ) -> None:
        """
        Create a new File.
        
        Args:
            fileBits: Array of data parts (like Blob).
            fileName: The name of the file.
            options: Optional configuration:
                     - type (str): MIME type
                     - lastModified (int): Timestamp in milliseconds
        """
        ...
    
    @property
    def name(self) -> str:
        """The name of the file."""
        ...
    
    @property
    def lastModified(self) -> int:
        """Last modified timestamp in milliseconds since epoch."""
        ...
    
    @property
    def webkitRelativePath(self) -> str:
        """Relative path from directory (if using webkitdirectory)."""
        ...


# =============================================================================
# FileReader Class
# =============================================================================

class FileReader:
    """
    Asynchronously read File or Blob contents.
    
    Example:
        reader = FileReader()
        
        def on_load(event):
            result = reader.result
            console.log(result)
        
        reader.onload = on_load
        reader.readAsText(file)
    
    Example (as data URL):
        reader = FileReader()
        reader.onload = lambda e: set_image_src(reader.result)
        reader.readAsDataURL(image_file)
    """
    
    # States
    EMPTY: int = 0
    LOADING: int = 1
    DONE: int = 2
    
    def __init__(self) -> None:
        """Create a new FileReader."""
        ...
    
    @property
    def readyState(self) -> int:
        """Current state: EMPTY, LOADING, or DONE."""
        ...
    
    @property
    def result(self) -> Optional[Union[str, ArrayBuffer]]:
        """The file contents after reading completes."""
        ...
    
    @property
    def error(self) -> Optional[Any]:
        """Error if reading failed."""
        ...
    
    # Event handlers (set to functions)
    onload: Optional[Any]
    onerror: Optional[Any]
    onabort: Optional[Any]
    onloadstart: Optional[Any]
    onloadend: Optional[Any]
    onprogress: Optional[Any]
    
    def readAsArrayBuffer(self, blob: Blob) -> None:
        """Read as ArrayBuffer."""
        ...
    
    def readAsDataURL(self, blob: Blob) -> None:
        """Read as base64 data URL."""
        ...
    
    def readAsText(self, blob: Blob, encoding: str = "utf-8") -> None:
        """Read as text string."""
        ...
    
    def abort(self) -> None:
        """Abort the read operation."""
        ...


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # ArrayBuffer
    "ArrayBuffer",
    
    # TypedArrays
    "Uint8Array",
    "Int8Array",
    "Uint8ClampedArray",
    "Int16Array",
    "Uint16Array",
    "Int32Array",
    "Uint32Array",
    "Float32Array",
    "Float64Array",
    "BigInt64Array",
    "BigUint64Array",
    
    # DataView
    "DataView",
    
    # Blob and File
    "Blob",
    "File",
    "FileReader",
]
