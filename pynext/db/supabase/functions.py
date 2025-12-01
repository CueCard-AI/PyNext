"""
PyNext Supabase Edge Functions.

Provides a simple API for invoking Supabase Edge Functions.

What are Edge Functions?
    Supabase Edge Functions are serverless TypeScript/JavaScript functions
    that run on Deno Deploy at the edge (close to your users).
    
    They're useful for:
    - Running custom backend logic
    - Integrating with third-party APIs
    - Complex data processing
    - Anything you can't do with RLS

Usage (Stupid Easy):
    from pynext.db.supabase import Supabase
    
    db = Supabase("https://xyz.supabase.co")
    
    # Invoke a function
    result = await db.functions.invoke("send-email", {
        "to": "user@example.com",
        "subject": "Hello!",
        "body": "Welcome to our app!"
    })
    
    print(result.data)  # Function response
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import json

from .exceptions import (
    FunctionError,
    FunctionNotFoundError,
    FunctionTimeoutError,
    FunctionInvocationError,
)

if TYPE_CHECKING:
    from .adapter import Supabase


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class FunctionResponse:
    """
    Response from an Edge Function invocation.
    
    Attributes:
        data: Response data from the function
        error: Error message if function failed
        status_code: HTTP status code
        headers: Response headers
    """
    data: Any = None
    error: Optional[str] = None
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_success(self) -> bool:
        """Check if the invocation was successful."""
        return self.error is None and 200 <= self.status_code < 300
    
    @property
    def is_error(self) -> bool:
        """Check if the invocation failed."""
        return not self.is_success
    
    def json(self) -> Any:
        """Get response data as parsed JSON."""
        if isinstance(self.data, str):
            return json.loads(self.data)
        return self.data
    
    def text(self) -> str:
        """Get response data as text."""
        if isinstance(self.data, bytes):
            return self.data.decode("utf-8")
        if isinstance(self.data, str):
            return self.data
        return json.dumps(self.data)
    
    def raise_for_status(self):
        """Raise exception if invocation failed."""
        if self.is_error:
            raise FunctionInvocationError(
                function_name="unknown",
                status_code=self.status_code,
                response_body=self.error or str(self.data),
            )


@dataclass
class FunctionsConfig:
    """
    Configuration for Edge Functions.
    
    Attributes:
        timeout: Request timeout in seconds
        retry_count: Number of retries on failure
        retry_delay: Delay between retries in seconds
        default_headers: Default headers for all requests
    """
    timeout: float = 30.0
    retry_count: int = 0
    retry_delay: float = 1.0
    default_headers: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Defensive copy of headers to prevent external mutation."""
        self.default_headers = dict(self.default_headers)


# =============================================================================
# MAIN FUNCTIONS CLASS
# =============================================================================

class SupabaseFunctions:
    """
    Supabase Edge Functions service.
    
    Invoke serverless functions deployed to your Supabase project.
    
    Usage:
        db = Supabase("https://xyz.supabase.co")
        
        # Simple invocation
        result = await db.functions.invoke("hello-world")
        print(result.data)
        
        # With payload
        result = await db.functions.invoke("process-order", {
            "order_id": "12345",
            "action": "confirm"
        })
        
        # With custom headers
        result = await db.functions.invoke(
            "webhook-handler",
            {"event": "purchase"},
            headers={"X-Webhook-Secret": "abc123"}
        )
    """
    
    def __init__(
        self,
        supabase: "Supabase",
        config: Optional[FunctionsConfig] = None,
    ):
        """
        Initialize functions service.
        
        Args:
            supabase: Parent Supabase adapter
            config: Functions configuration
        """
        self._supabase = supabase
        self._config = config or FunctionsConfig()
    
    @property
    def _client(self):
        """Get the underlying supabase-py functions client."""
        self._supabase._ensure_initialized()
        return self._supabase.client.functions
    
    async def invoke(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
        region: Optional[str] = None,
        method: str = "POST",
    ) -> FunctionResponse:
        """
        Invoke an Edge Function.
        
        Args:
            function_name: Name of the function to invoke
            payload: JSON payload to send to the function
            headers: Additional headers for this request
            timeout: Request timeout (overrides default)
            region: Specific region to invoke in
            method: HTTP method (default: POST)
        
        Returns:
            FunctionResponse with data or error
        
        Raises:
            FunctionNotFoundError: If function doesn't exist
            FunctionTimeoutError: If request times out
            FunctionInvocationError: If function returns an error
        
        Example:
            # Simple invocation
            result = await db.functions.invoke("hello")
            
            # With data
            result = await db.functions.invoke("process", {
                "user_id": 123,
                "action": "upgrade"
            })
            
            if result.is_success:
                print(result.data)
            else:
                print(f"Error: {result.error}")
        """
        try:
            # Merge headers
            final_headers = dict(self._config.default_headers)
            if headers:
                final_headers.update(headers)
            
            # Add region header if specified
            if region:
                final_headers["x-region"] = region
            
            # Build invoke options
            invoke_options = {
                "body": payload,
                "headers": final_headers if final_headers else None,
            }
            
            # Invoke the function
            response = self._client.invoke(function_name, invoke_options)
            
            # Parse response
            return FunctionResponse(
                data=response,
                status_code=200,
            )
            
        except Exception as e:
            return self._handle_error(function_name, e)
    
    async def invoke_with_retry(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        headers: Optional[Dict[str, str]] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ) -> FunctionResponse:
        """
        Invoke a function with automatic retries.
        
        Args:
            function_name: Name of the function
            payload: JSON payload
            headers: Additional headers
            max_retries: Number of retry attempts
            retry_delay: Delay between retries
        
        Returns:
            FunctionResponse
        
        Example:
            # Retry up to 3 times with 1s delay
            result = await db.functions.invoke_with_retry(
                "critical-operation",
                {"data": "important"},
                max_retries=3,
                retry_delay=1.0
            )
        """
        import asyncio
        
        retries = max_retries if max_retries is not None else self._config.retry_count
        delay = retry_delay if retry_delay is not None else self._config.retry_delay
        
        last_error = None
        
        for attempt in range(retries + 1):
            result = await self.invoke(function_name, payload, headers=headers)
            
            if result.is_success:
                return result
            
            last_error = result
            
            if attempt < retries:
                await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff
        
        return last_error or FunctionResponse(
            error="Max retries exceeded",
            status_code=500,
        )
    
    def _handle_error(
        self,
        function_name: str,
        error: Exception,
    ) -> FunctionResponse:
        """Handle and categorize function errors."""
        error_str = str(error).lower()
        
        # Check for specific error types
        if "not found" in error_str or "404" in error_str:
            raise FunctionNotFoundError(function_name=function_name)
        
        if "timeout" in error_str or "timed out" in error_str:
            raise FunctionTimeoutError(
                function_name=function_name,
                timeout_seconds=self._config.timeout,
            )
        
        # Generic invocation error
        return FunctionResponse(
            error=str(error),
            status_code=500,
        )
    
    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================
    
    async def invoke_json(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """
        Invoke a function and return parsed JSON response.
        
        Args:
            function_name: Name of the function
            payload: JSON payload
            **kwargs: Additional invoke options
        
        Returns:
            Parsed JSON response
        
        Raises:
            FunctionError: If invocation fails
        
        Example:
            data = await db.functions.invoke_json("get-user-stats", {"user_id": 123})
            print(data["total_orders"])
        """
        result = await self.invoke(function_name, payload, **kwargs)
        
        if result.is_error:
            raise FunctionInvocationError(
                function_name=function_name,
                status_code=result.status_code,
                response_body=result.error or "",
            )
        
        return result.json()
    
    async def invoke_text(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        """
        Invoke a function and return text response.
        
        Args:
            function_name: Name of the function
            payload: JSON payload
            **kwargs: Additional invoke options
        
        Returns:
            Text response
        
        Raises:
            FunctionError: If invocation fails
        """
        result = await self.invoke(function_name, payload, **kwargs)
        
        if result.is_error:
            raise FunctionInvocationError(
                function_name=function_name,
                status_code=result.status_code,
                response_body=result.error or "",
            )
        
        return result.text()
    
    async def health_check(self, function_name: str) -> bool:
        """
        Check if a function is healthy and responding.
        
        Args:
            function_name: Name of the function
        
        Returns:
            True if function responds successfully
        
        Example:
            if await db.functions.health_check("critical-function"):
                print("Function is healthy")
        """
        try:
            result = await self.invoke(function_name, {"health_check": True})
            return result.is_success
        except FunctionNotFoundError:
            return False
        except Exception:
            return False

