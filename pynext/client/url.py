"""
PyNext URL API - Type Stubs for URL and URLSearchParams

=============================================================================
WHO
=============================================================================

Developers who need to:
- Parse and manipulate URLs
- Build API endpoints with query parameters
- Handle routing and navigation
- Work with browser location

=============================================================================
WHAT
=============================================================================

Python type stubs for the Web URL API:
- URL: Parse and manipulate URLs with full component access
- URLSearchParams: Query string manipulation with iteration support

=============================================================================
WHEN
=============================================================================

Use these APIs when you need to:
- Construct API URLs with dynamic parameters
- Parse query strings from window.location
- Resolve relative URLs against a base
- Build download links with URL.createObjectURL

=============================================================================
WHERE
=============================================================================

Client-side code decorated with @client that transpiles to JavaScript.
These are browser-native APIs available in all modern browsers.

=============================================================================
WHY
=============================================================================

- **Type Safety**: Full IDE autocompletion for all URL properties
- **Zero Runtime**: Direct passthrough to native browser APIs
- **Pythonic**: Works with str(), iteration, and familiar patterns
- **AI-Friendly**: Comprehensive docstrings for LLM assistance

=============================================================================
HOW (Transpilation)
=============================================================================

All URL APIs transpile directly to JavaScript without any wrappers:

    Python:
        url = URL("https://example.com/path?page=1")
        url.searchParams.get("page")
        url.pathname = "/new"
    
    JavaScript (transpiled):
        let url = new URL("https://example.com/path?page=1");
        url.searchParams.get("page");
        url.pathname = "/new";

The transpiler recognizes URL and URLSearchParams in DOM_GLOBALS,
and their methods/properties in DOM_METHODS/DOM_PROPERTIES, ensuring
zero-runtime passthrough.

=============================================================================
"""

from typing import Optional, Iterator, Union, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .binary import Blob


# =============================================================================
# URL Class
# =============================================================================

class URL:
    """
    Parse and manipulate URLs with full access to all components.
    
    WHO: Developers working with URLs for navigation, APIs, or routing
    WHAT: Full URL parsing and manipulation API
    WHEN: Building API endpoints, parsing location, creating downloads
    WHERE: Client-side transpiled code
    WHY: Type-safe, zero-runtime URL handling
    HOW: Direct passthrough to native URL API
    
    Example (Basic Usage):
        url = URL("https://example.com:8080/path?foo=bar#section")
        
        url.hostname    # "example.com"
        url.port        # "8080"
        url.pathname    # "/path"
        url.search      # "?foo=bar"
        url.hash        # "#section"
        url.origin      # "https://example.com:8080"
    
    Example (Modify URL):
        url = URL("https://api.example.com/v1/users")
        url.pathname = "/v2/accounts"
        url.searchParams.set("limit", "10")
        # url.href is now "https://api.example.com/v2/accounts?limit=10"
    
    Example (Resolve Relative URL):
        base = URL("https://example.com/a/b/c")
        relative = URL("../d", base)
        relative.href  # "https://example.com/a/d"
    
    Example (Create Download Link):
        blob = Blob([data], {"type": "text/csv"})
        url = URL.createObjectURL(blob)
        # Use url for download, then:
        URL.revokeObjectURL(url)
    """
    
    def __init__(self, url: str, base: Optional[Union[str, "URL"]] = None) -> None:
        """
        Create a new URL object.
        
        Args:
            url: The URL string to parse. Can be absolute or relative.
            base: Optional base URL for resolving relative URLs.
                  Required if url is relative.
        
        Raises:
            TypeError: If url is not a valid URL and no base is provided.
        
        Example:
            # Absolute URL
            url = URL("https://example.com/path")
            
            # Relative URL with base
            url = URL("/api/users", "https://example.com")
            url.href  # "https://example.com/api/users"
            
            # Relative path resolution
            url = URL("../images/logo.png", "https://example.com/css/style.css")
            url.href  # "https://example.com/images/logo.png"
        """
        ...
    
    # =========================================================================
    # Read/Write Properties
    # =========================================================================
    
    @property
    def href(self) -> str:
        """
        The full URL string.
        
        Setting this property re-parses the entire URL.
        
        Example:
            url = URL("https://example.com")
            url.href  # "https://example.com/"
            url.href = "https://other.com/path"
            url.hostname  # "other.com"
        """
        ...
    
    @href.setter
    def href(self, value: str) -> None:
        """Set the full URL string (re-parses everything)."""
        ...
    
    @property
    def protocol(self) -> str:
        """
        The protocol/scheme with trailing colon.
        
        Example:
            URL("https://example.com").protocol  # "https:"
            URL("ftp://files.com").protocol      # "ftp:"
        """
        ...
    
    @protocol.setter
    def protocol(self, value: str) -> None:
        """Set the protocol (include the colon)."""
        ...
    
    @property
    def username(self) -> str:
        """
        The username portion before the host.
        
        Example:
            URL("https://user:pass@example.com").username  # "user"
        """
        ...
    
    @username.setter
    def username(self, value: str) -> None:
        """Set the username."""
        ...
    
    @property
    def password(self) -> str:
        """
        The password portion before the host.
        
        Example:
            URL("https://user:pass@example.com").password  # "pass"
        """
        ...
    
    @password.setter
    def password(self, value: str) -> None:
        """Set the password."""
        ...
    
    @property
    def host(self) -> str:
        """
        The hostname and port combined.
        
        Example:
            URL("https://example.com:8080/path").host  # "example.com:8080"
            URL("https://example.com/path").host       # "example.com"
        """
        ...
    
    @host.setter
    def host(self, value: str) -> None:
        """Set the host (hostname:port)."""
        ...
    
    @property
    def hostname(self) -> str:
        """
        The hostname without port.
        
        Example:
            URL("https://example.com:8080/path").hostname  # "example.com"
        """
        ...
    
    @hostname.setter
    def hostname(self, value: str) -> None:
        """Set the hostname."""
        ...
    
    @property
    def port(self) -> str:
        """
        The port number as a string.
        
        Empty string if using default port for protocol.
        
        Example:
            URL("https://example.com:8080").port  # "8080"
            URL("https://example.com").port       # ""
        """
        ...
    
    @port.setter
    def port(self, value: str) -> None:
        """Set the port number."""
        ...
    
    @property
    def pathname(self) -> str:
        """
        The path portion of the URL.
        
        Always starts with "/" for URLs with authority.
        
        Example:
            URL("https://example.com/api/users").pathname  # "/api/users"
            URL("https://example.com").pathname            # "/"
        """
        ...
    
    @pathname.setter
    def pathname(self, value: str) -> None:
        """Set the pathname."""
        ...
    
    @property
    def search(self) -> str:
        """
        The query string including the leading "?".
        
        Empty string if no query parameters.
        
        Example:
            URL("https://example.com?foo=1&bar=2").search  # "?foo=1&bar=2"
            URL("https://example.com").search              # ""
        """
        ...
    
    @search.setter
    def search(self, value: str) -> None:
        """Set the query string (updates searchParams too)."""
        ...
    
    @property
    def hash(self) -> str:
        """
        The fragment identifier including the leading "#".
        
        Empty string if no fragment.
        
        Example:
            URL("https://example.com#section").hash  # "#section"
            URL("https://example.com").hash          # ""
        """
        ...
    
    @hash.setter
    def hash(self, value: str) -> None:
        """Set the fragment identifier."""
        ...
    
    # =========================================================================
    # Read-Only Properties
    # =========================================================================
    
    @property
    def origin(self) -> str:
        """
        The origin of the URL (protocol + host). Read-only.
        
        Example:
            URL("https://example.com:8080/path").origin  # "https://example.com:8080"
        """
        ...
    
    @property
    def searchParams(self) -> "URLSearchParams":
        """
        URLSearchParams object for the query string. Read-only.
        
        Modifications to searchParams automatically update url.search.
        
        Example:
            url = URL("https://example.com?page=1")
            url.searchParams.get("page")    # "1"
            url.searchParams.set("page", "2")
            url.search  # "?page=2"
        """
        ...
    
    # =========================================================================
    # Methods
    # =========================================================================
    
    def toString(self) -> str:
        """
        Return the URL as a string. Same as href.
        
        Example:
            url = URL("https://example.com/path")
            url.toString()  # "https://example.com/path"
            str(url)        # Same result (Python magic method)
        """
        ...
    
    def toJSON(self) -> str:
        """
        Return the URL as a string for JSON serialization.
        
        Same as href. Used by JSON.stringify().
        
        Example:
            url = URL("https://example.com")
            url.toJSON()  # "https://example.com/"
        """
        ...
    
    def __str__(self) -> str:
        """Python string conversion - returns href."""
        ...
    
    # =========================================================================
    # Static Methods
    # =========================================================================
    
    @staticmethod
    def createObjectURL(blob: "Blob") -> str:
        """
        Create a URL representing the given Blob.
        
        The URL is only valid for the document's lifetime.
        Call revokeObjectURL() when done to free memory.
        
        Args:
            blob: A Blob or File object.
        
        Returns:
            A blob: URL string.
        
        Example:
            blob = Blob([csv_data], {"type": "text/csv"})
            url = URL.createObjectURL(blob)
            
            # Use for download
            a = document.createElement("a")
            a.href = url
            a.download = "data.csv"
            a.click()
            
            # Clean up
            URL.revokeObjectURL(url)
        """
        ...
    
    @staticmethod
    def revokeObjectURL(url: str) -> None:
        """
        Release a URL created by createObjectURL().
        
        Call this when you're done with the blob URL to free memory.
        After calling, the URL is no longer valid.
        
        Args:
            url: A URL previously created by createObjectURL().
        
        Example:
            url = URL.createObjectURL(blob)
            # ... use url ...
            URL.revokeObjectURL(url)  # Free memory
        """
        ...


# =============================================================================
# URLSearchParams Class
# =============================================================================

class URLSearchParams:
    """
    Utility class for working with query strings.
    
    WHO: Developers manipulating URL query parameters
    WHAT: CRUD operations on query string key-value pairs
    WHEN: Building API URLs, reading page parameters, filtering
    WHERE: Client-side transpiled code
    WHY: Type-safe query string manipulation with iteration
    HOW: Direct passthrough to native URLSearchParams API
    
    Example (Create from string):
        params = URLSearchParams("foo=1&bar=2&foo=3")
        params.get("foo")     # "1" (first value)
        params.getAll("foo")  # ["1", "3"] (all values)
    
    Example (Create from dict):
        params = URLSearchParams({"page": "1", "limit": "10"})
        params.toString()  # "page=1&limit=10"
    
    Example (Create from tuples):
        params = URLSearchParams([("tag", "python"), ("tag", "web")])
        params.getAll("tag")  # ["python", "web"]
    
    Example (Modify):
        params = URLSearchParams()
        params.set("page", "1")
        params.append("filter", "active")
        params.append("filter", "recent")
        params.toString()  # "page=1&filter=active&filter=recent"
    
    Example (Iterate):
        params = URLSearchParams("a=1&b=2&c=3")
        for key, value in params.entries():
            print(f"{key}={value}")
    """
    
    def __init__(self, init: Optional[Union[str, dict, list]] = None) -> None:
        """
        Create a new URLSearchParams object.
        
        Args:
            init: Initial query string data. Can be:
                  - String: "foo=1&bar=2" (with or without leading "?")
                  - Dict: {"foo": "1", "bar": "2"}
                  - List of tuples: [("foo", "1"), ("bar", "2")]
                  - None: Empty params
        
        Example:
            # From string
            params = URLSearchParams("page=1&sort=name")
            
            # From dict
            params = URLSearchParams({"page": "1", "sort": "name"})
            
            # From tuples (allows duplicate keys)
            params = URLSearchParams([("tag", "a"), ("tag", "b")])
            
            # Empty
            params = URLSearchParams()
        """
        ...
    
    # =========================================================================
    # Read Methods
    # =========================================================================
    
    def get(self, name: str) -> Optional[str]:
        """
        Get the first value for a parameter.
        
        Args:
            name: The parameter name.
        
        Returns:
            The first value, or None if not found.
        
        Example:
            params = URLSearchParams("foo=1&foo=2")
            params.get("foo")      # "1" (first value)
            params.get("missing")  # None
        """
        ...
    
    def getAll(self, name: str) -> list:
        """
        Get all values for a parameter.
        
        Args:
            name: The parameter name.
        
        Returns:
            List of all values (empty list if not found).
        
        Example:
            params = URLSearchParams("tag=a&tag=b&tag=c")
            params.getAll("tag")      # ["a", "b", "c"]
            params.getAll("missing")  # []
        """
        ...
    
    def has(self, name: str, value: Optional[str] = None) -> bool:
        """
        Check if a parameter exists.
        
        Args:
            name: The parameter name.
            value: Optional specific value to check for.
        
        Returns:
            True if the parameter exists (with the value, if specified).
        
        Example:
            params = URLSearchParams("foo=1&bar=2")
            params.has("foo")        # True
            params.has("missing")    # False
            params.has("foo", "1")   # True
            params.has("foo", "99")  # False
        """
        ...
    
    # =========================================================================
    # Write Methods
    # =========================================================================
    
    def set(self, name: str, value: str) -> None:
        """
        Set a parameter value, replacing all existing values.
        
        Args:
            name: The parameter name.
            value: The new value.
        
        Example:
            params = URLSearchParams("foo=1&foo=2")
            params.set("foo", "new")
            params.toString()  # "foo=new"
        """
        ...
    
    def append(self, name: str, value: str) -> None:
        """
        Add a new parameter value (keeps existing values).
        
        Args:
            name: The parameter name.
            value: The value to add.
        
        Example:
            params = URLSearchParams("foo=1")
            params.append("foo", "2")
            params.toString()  # "foo=1&foo=2"
        """
        ...
    
    def delete(self, name: str, value: Optional[str] = None) -> None:
        """
        Delete a parameter.
        
        Args:
            name: The parameter name.
            value: Optional specific value to delete. If omitted,
                   deletes all values for the name.
        
        Example:
            params = URLSearchParams("foo=1&foo=2&bar=3")
            params.delete("foo")
            params.toString()  # "bar=3"
            
            params = URLSearchParams("foo=1&foo=2")
            params.delete("foo", "1")  # Delete only foo=1
            params.toString()  # "foo=2"
        """
        ...
    
    def sort(self) -> None:
        """
        Sort all parameters alphabetically by name.
        
        Stable sort - values with the same name keep their order.
        
        Example:
            params = URLSearchParams("z=3&a=1&m=2")
            params.sort()
            params.toString()  # "a=1&m=2&z=3"
        """
        ...
    
    # =========================================================================
    # Iteration Methods
    # =========================================================================
    
    def keys(self) -> Iterator[str]:
        """
        Iterate over all parameter names.
        
        May include duplicates if a name has multiple values.
        
        Example:
            params = URLSearchParams("a=1&b=2&a=3")
            list(params.keys())  # ["a", "b", "a"]
        """
        ...
    
    def values(self) -> Iterator[str]:
        """
        Iterate over all parameter values.
        
        Example:
            params = URLSearchParams("a=1&b=2&c=3")
            list(params.values())  # ["1", "2", "3"]
        """
        ...
    
    def entries(self) -> Iterator[tuple]:
        """
        Iterate over all key-value pairs.
        
        Example:
            params = URLSearchParams("a=1&b=2")
            for key, value in params.entries():
                print(f"{key}={value}")
            # Output:
            # a=1
            # b=2
        """
        ...
    
    def forEach(self, callback: Any) -> None:
        """
        Execute a callback for each parameter.
        
        Args:
            callback: Function(value, name, searchParams)
        
        Example:
            def log_param(value, name, params):
                console.log(f"{name}: {value}")
            
            params.forEach(log_param)
        """
        ...
    
    # =========================================================================
    # Conversion Methods
    # =========================================================================
    
    def toString(self) -> str:
        """
        Convert to query string format (without leading "?").
        
        Example:
            params = URLSearchParams({"page": "1", "sort": "name"})
            params.toString()  # "page=1&sort=name"
        """
        ...
    
    def __str__(self) -> str:
        """Python string conversion - same as toString()."""
        ...
    
    def __iter__(self) -> Iterator[tuple]:
        """Python iteration - same as entries()."""
        ...


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "URL",
    "URLSearchParams",
]

