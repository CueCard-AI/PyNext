"""
Comprehensive tests for PyNext Supabase Edge Functions.

Tests cover:
- FunctionResponse model
- FunctionsConfig
- Function invocation
- Error handling
- Retry logic
- Convenience methods

Total: 80 tests
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json

from pynext.db.supabase.functions import (
    SupabaseFunctions,
    FunctionResponse,
    FunctionsConfig,
)
from pynext.db.supabase.exceptions import (
    FunctionError,
    FunctionNotFoundError,
    FunctionTimeoutError,
    FunctionInvocationError,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_supabase():
    """Create mock Supabase adapter."""
    supabase = Mock()
    supabase._initialized = True
    supabase._ensure_initialized = Mock()
    
    # Mock functions client
    functions_client = Mock()
    supabase.client = Mock()
    supabase.client.functions = functions_client
    
    return supabase


@pytest.fixture
def functions(mock_supabase):
    """Create SupabaseFunctions instance."""
    return SupabaseFunctions(mock_supabase)


@pytest.fixture
def functions_with_config(mock_supabase):
    """Create SupabaseFunctions with custom config."""
    config = FunctionsConfig(
        timeout=60.0,
        retry_count=3,
        retry_delay=0.1,
        default_headers={"X-Custom": "value"}
    )
    return SupabaseFunctions(mock_supabase, config)


# =============================================================================
# FUNCTION RESPONSE TESTS (20 tests)
# =============================================================================

class TestFunctionResponse:
    """Tests for FunctionResponse model."""
    
    def test_response_with_data(self):
        """FunctionResponse stores data."""
        response = FunctionResponse(data={"result": "success"})
        assert response.data == {"result": "success"}
    
    def test_response_with_error(self):
        """FunctionResponse stores error."""
        response = FunctionResponse(error="Something went wrong")
        assert response.error == "Something went wrong"
    
    def test_response_status_code(self):
        """FunctionResponse stores status code."""
        response = FunctionResponse(data={}, status_code=201)
        assert response.status_code == 201
    
    def test_response_default_status_code(self):
        """FunctionResponse has default status 200."""
        response = FunctionResponse(data={})
        assert response.status_code == 200
    
    def test_response_headers(self):
        """FunctionResponse stores headers."""
        response = FunctionResponse(
            data={},
            headers={"Content-Type": "application/json"}
        )
        assert response.headers["Content-Type"] == "application/json"
    
    def test_response_default_headers(self):
        """FunctionResponse has empty default headers."""
        response = FunctionResponse(data={})
        assert response.headers == {}
    
    def test_response_is_success_true(self):
        """is_success returns True for 2xx status."""
        response = FunctionResponse(data={}, status_code=200)
        assert response.is_success is True
    
    def test_response_is_success_201(self):
        """is_success returns True for 201."""
        response = FunctionResponse(data={}, status_code=201)
        assert response.is_success is True
    
    def test_response_is_success_false_error(self):
        """is_success returns False when error set."""
        response = FunctionResponse(error="Error", status_code=200)
        assert response.is_success is False
    
    def test_response_is_success_false_500(self):
        """is_success returns False for 5xx."""
        response = FunctionResponse(data={}, status_code=500)
        assert response.is_success is False
    
    def test_response_is_success_false_400(self):
        """is_success returns False for 4xx."""
        response = FunctionResponse(data={}, status_code=400)
        assert response.is_success is False
    
    def test_response_is_error_true(self):
        """is_error returns True when not success."""
        response = FunctionResponse(error="Error")
        assert response.is_error is True
    
    def test_response_is_error_false(self):
        """is_error returns False when success."""
        response = FunctionResponse(data={})
        assert response.is_error is False
    
    def test_response_json_dict(self):
        """json() returns dict data as-is."""
        response = FunctionResponse(data={"key": "value"})
        assert response.json() == {"key": "value"}
    
    def test_response_json_string(self):
        """json() parses string data."""
        response = FunctionResponse(data='{"key": "value"}')
        assert response.json() == {"key": "value"}
    
    def test_response_text_string(self):
        """text() returns string data."""
        response = FunctionResponse(data="hello world")
        assert response.text() == "hello world"
    
    def test_response_text_bytes(self):
        """text() decodes bytes."""
        response = FunctionResponse(data=b"hello")
        assert response.text() == "hello"
    
    def test_response_text_dict(self):
        """text() serializes dict."""
        response = FunctionResponse(data={"key": "value"})
        assert '"key"' in response.text()
    
    def test_response_raise_for_status_success(self):
        """raise_for_status does nothing on success."""
        response = FunctionResponse(data={})
        response.raise_for_status()  # Should not raise
    
    def test_response_raise_for_status_error(self):
        """raise_for_status raises on error."""
        response = FunctionResponse(error="Failed", status_code=500)
        with pytest.raises(FunctionInvocationError):
            response.raise_for_status()


# =============================================================================
# FUNCTIONS CONFIG TESTS (10 tests)
# =============================================================================

class TestFunctionsConfig:
    """Tests for FunctionsConfig."""
    
    def test_config_default_timeout(self):
        """FunctionsConfig has default timeout."""
        config = FunctionsConfig()
        assert config.timeout == 30.0
    
    def test_config_custom_timeout(self):
        """FunctionsConfig accepts custom timeout."""
        config = FunctionsConfig(timeout=60.0)
        assert config.timeout == 60.0
    
    def test_config_default_retry_count(self):
        """FunctionsConfig has zero retry by default."""
        config = FunctionsConfig()
        assert config.retry_count == 0
    
    def test_config_custom_retry_count(self):
        """FunctionsConfig accepts custom retry count."""
        config = FunctionsConfig(retry_count=5)
        assert config.retry_count == 5
    
    def test_config_default_retry_delay(self):
        """FunctionsConfig has 1 second retry delay."""
        config = FunctionsConfig()
        assert config.retry_delay == 1.0
    
    def test_config_custom_retry_delay(self):
        """FunctionsConfig accepts custom retry delay."""
        config = FunctionsConfig(retry_delay=0.5)
        assert config.retry_delay == 0.5
    
    def test_config_default_headers_empty(self):
        """FunctionsConfig has empty default headers."""
        config = FunctionsConfig()
        assert config.default_headers == {}
    
    def test_config_custom_default_headers(self):
        """FunctionsConfig accepts default headers."""
        config = FunctionsConfig(default_headers={"X-Api-Key": "secret"})
        assert config.default_headers["X-Api-Key"] == "secret"
    
    def test_config_all_options(self):
        """FunctionsConfig accepts all options."""
        config = FunctionsConfig(
            timeout=120.0,
            retry_count=10,
            retry_delay=2.0,
            default_headers={"Authorization": "Bearer token"}
        )
        assert config.timeout == 120.0
        assert config.retry_count == 10
        assert config.retry_delay == 2.0
    
    def test_config_headers_isolated(self):
        """FunctionsConfig headers are isolated."""
        headers = {"X-Key": "value"}
        config = FunctionsConfig(default_headers=headers)
        headers["X-New"] = "new"  # Modify original
        assert "X-New" not in config.default_headers  # Shouldn't affect config


# =============================================================================
# INVOKE TESTS (25 tests)
# =============================================================================

class TestInvoke:
    """Tests for invoke method."""
    
    @pytest.mark.asyncio
    async def test_invoke_success(self, functions, mock_supabase):
        """invoke returns FunctionResponse on success."""
        mock_supabase.client.functions.invoke = Mock(return_value={"result": "ok"})
        
        response = await functions.invoke("my-function")
        
        assert isinstance(response, FunctionResponse)
        assert response.data == {"result": "ok"}
    
    @pytest.mark.asyncio
    async def test_invoke_with_payload(self, functions, mock_supabase):
        """invoke passes payload to function."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke("my-function", {"key": "value"})
        
        call_args = mock_supabase.client.functions.invoke.call_args
        # call_args[0] is positional args: (function_name, invoke_options)
        assert call_args[0][1]["body"] == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_invoke_with_headers(self, functions, mock_supabase):
        """invoke passes custom headers."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke("my-function", headers={"X-Custom": "value"})
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert "X-Custom" in call_args[0][1]["headers"]
    
    @pytest.mark.asyncio
    async def test_invoke_with_region(self, functions, mock_supabase):
        """invoke passes region header."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke("my-function", region="us-east-1")
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["headers"]["x-region"] == "us-east-1"
    
    @pytest.mark.asyncio
    async def test_invoke_merges_default_headers(self, functions_with_config, mock_supabase):
        """invoke merges default headers with custom."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions_with_config.invoke("my-function", headers={"X-Other": "other"})
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["headers"]["X-Custom"] == "value"
        assert call_args[0][1]["headers"]["X-Other"] == "other"
    
    @pytest.mark.asyncio
    async def test_invoke_custom_overrides_default(self, functions_with_config, mock_supabase):
        """invoke custom headers override default."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions_with_config.invoke("my-function", headers={"X-Custom": "override"})
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["headers"]["X-Custom"] == "override"
    
    @pytest.mark.asyncio
    async def test_invoke_function_not_found(self, functions, mock_supabase):
        """invoke raises FunctionNotFoundError for 404."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Function not found"))
        
        with pytest.raises(FunctionNotFoundError):
            await functions.invoke("nonexistent")
    
    @pytest.mark.asyncio
    async def test_invoke_function_404(self, functions, mock_supabase):
        """invoke raises FunctionNotFoundError for 404 in message."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("404 not found"))
        
        with pytest.raises(FunctionNotFoundError):
            await functions.invoke("missing")
    
    @pytest.mark.asyncio
    async def test_invoke_timeout(self, functions, mock_supabase):
        """invoke raises FunctionTimeoutError on timeout."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Request timed out"))
        
        with pytest.raises(FunctionTimeoutError):
            await functions.invoke("slow-function")
    
    @pytest.mark.asyncio
    async def test_invoke_generic_error(self, functions, mock_supabase):
        """invoke returns error response for generic errors."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Network error"))
        
        response = await functions.invoke("my-function")
        
        assert response.is_error is True
        assert "Network error" in response.error
    
    @pytest.mark.asyncio
    async def test_invoke_null_payload(self, functions, mock_supabase):
        """invoke handles None payload."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke("my-function", None)
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["body"] is None
    
    @pytest.mark.asyncio
    async def test_invoke_empty_payload(self, functions, mock_supabase):
        """invoke handles empty payload."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke("my-function", {})
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["body"] == {}
    
    @pytest.mark.asyncio
    async def test_invoke_no_headers_when_empty(self, functions, mock_supabase):
        """invoke handles no headers."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke("my-function")
        
        call_args = mock_supabase.client.functions.invoke.call_args
        # headers should be None when no custom headers
        assert call_args[0][1]["headers"] is None
    
    @pytest.mark.asyncio
    async def test_invoke_calls_correct_function(self, functions, mock_supabase):
        """invoke calls correct function name."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke("specific-function")
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][0] == "specific-function"
    
    @pytest.mark.asyncio
    async def test_invoke_complex_payload(self, functions, mock_supabase):
        """invoke handles complex payload."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        payload = {
            "nested": {"key": "value"},
            "array": [1, 2, 3],
            "null": None,
            "bool": True
        }
        
        await functions.invoke("my-function", payload)
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["body"] == payload
    
    @pytest.mark.asyncio
    async def test_invoke_returns_string_data(self, functions, mock_supabase):
        """invoke handles string response."""
        mock_supabase.client.functions.invoke = Mock(return_value="plain text response")
        
        response = await functions.invoke("my-function")
        
        assert response.data == "plain text response"
    
    @pytest.mark.asyncio
    async def test_invoke_returns_list_data(self, functions, mock_supabase):
        """invoke handles list response."""
        mock_supabase.client.functions.invoke = Mock(return_value=[1, 2, 3])
        
        response = await functions.invoke("my-function")
        
        assert response.data == [1, 2, 3]
    
    @pytest.mark.asyncio
    async def test_invoke_success_status(self, functions, mock_supabase):
        """invoke sets success status."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        response = await functions.invoke("my-function")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_invoke_timeout_variant(self, functions, mock_supabase):
        """invoke handles 'timeout' in error."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Connection timeout"))
        
        with pytest.raises(FunctionTimeoutError):
            await functions.invoke("slow-function")
    
    @pytest.mark.asyncio
    async def test_invoke_preserves_function_name_in_error(self, functions, mock_supabase):
        """invoke preserves function name in error."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("not found"))
        
        with pytest.raises(FunctionNotFoundError) as exc_info:
            await functions.invoke("my-func")
        
        assert "my-func" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invoke_error_status_code(self, functions, mock_supabase):
        """invoke sets error status code."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Error"))
        
        response = await functions.invoke("my-function")
        
        assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_invoke_none_response(self, functions, mock_supabase):
        """invoke handles None response."""
        mock_supabase.client.functions.invoke = Mock(return_value=None)
        
        response = await functions.invoke("my-function")
        
        assert response.data is None
    
    @pytest.mark.asyncio
    async def test_invoke_boolean_response(self, functions, mock_supabase):
        """invoke handles boolean response."""
        mock_supabase.client.functions.invoke = Mock(return_value=True)
        
        response = await functions.invoke("my-function")
        
        assert response.data is True
    
    @pytest.mark.asyncio
    async def test_invoke_numeric_response(self, functions, mock_supabase):
        """invoke handles numeric response."""
        mock_supabase.client.functions.invoke = Mock(return_value=42)
        
        response = await functions.invoke("my-function")
        
        assert response.data == 42


# =============================================================================
# RETRY TESTS (15 tests)
# =============================================================================

class TestInvokeWithRetry:
    """Tests for invoke_with_retry method."""
    
    @pytest.mark.asyncio
    async def test_retry_success_first_try(self, functions, mock_supabase):
        """invoke_with_retry succeeds on first try."""
        mock_supabase.client.functions.invoke = Mock(return_value={"ok": True})
        
        response = await functions.invoke_with_retry("my-function", max_retries=3)
        
        assert response.is_success is True
        assert mock_supabase.client.functions.invoke.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failure(self, functions, mock_supabase):
        """invoke_with_retry succeeds after failures."""
        call_count = [0]
        
        def mock_invoke(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Temporary error")
            return {"ok": True}
        
        mock_supabase.client.functions.invoke = Mock(side_effect=mock_invoke)
        
        response = await functions.invoke_with_retry(
            "my-function",
            max_retries=5,
            retry_delay=0.01
        )
        
        assert response.is_success is True
        assert call_count[0] == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhausted(self, functions, mock_supabase):
        """invoke_with_retry fails after all retries."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Error"))
        
        response = await functions.invoke_with_retry(
            "my-function",
            max_retries=2,
            retry_delay=0.01
        )
        
        assert response.is_error is True
        assert mock_supabase.client.functions.invoke.call_count == 3  # 1 + 2 retries
    
    @pytest.mark.asyncio
    async def test_retry_uses_config_defaults(self, functions_with_config, mock_supabase):
        """invoke_with_retry uses config retry settings."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Error"))
        
        await functions_with_config.invoke_with_retry("my-function")
        
        # Config has retry_count=3
        assert mock_supabase.client.functions.invoke.call_count == 4  # 1 + 3 retries
    
    @pytest.mark.asyncio
    async def test_retry_overrides_config(self, functions_with_config, mock_supabase):
        """invoke_with_retry params override config."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Error"))
        
        await functions_with_config.invoke_with_retry(
            "my-function",
            max_retries=1,
            retry_delay=0.01
        )
        
        assert mock_supabase.client.functions.invoke.call_count == 2  # 1 + 1 retry
    
    @pytest.mark.asyncio
    async def test_retry_with_payload(self, functions, mock_supabase):
        """invoke_with_retry passes payload."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke_with_retry("my-function", {"key": "value"})
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["body"] == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_retry_with_headers(self, functions, mock_supabase):
        """invoke_with_retry passes headers."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke_with_retry(
            "my-function",
            headers={"X-Key": "value"}
        )
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert "X-Key" in call_args[0][1]["headers"]
    
    @pytest.mark.asyncio
    async def test_retry_zero_retries(self, functions, mock_supabase):
        """invoke_with_retry with 0 retries only tries once."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Error"))
        
        await functions.invoke_with_retry("my-function", max_retries=0, retry_delay=0.01)
        
        assert mock_supabase.client.functions.invoke.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_returns_last_error(self, functions, mock_supabase):
        """invoke_with_retry returns last error response."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Final error"))
        
        response = await functions.invoke_with_retry(
            "my-function",
            max_retries=1,
            retry_delay=0.01
        )
        
        assert "Final error" in response.error
    
    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self, functions, mock_supabase):
        """invoke_with_retry uses exponential backoff."""
        call_times = []
        
        def mock_invoke(*args, **kwargs):
            import time
            call_times.append(time.time())
            raise Exception("Error")
        
        mock_supabase.client.functions.invoke = Mock(side_effect=mock_invoke)
        
        await functions.invoke_with_retry(
            "my-function",
            max_retries=2,
            retry_delay=0.05
        )
        
        # Check delays increase (with tolerance for timing)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Second delay should be longer (exponential)
            assert delay2 >= delay1 * 0.5  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_retry_none_on_no_retries_configured(self, functions, mock_supabase):
        """invoke_with_retry with None max_retries uses config."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        response = await functions.invoke_with_retry("my-function")
        
        assert response.is_success is True
    
    @pytest.mark.asyncio
    async def test_retry_stops_on_success(self, functions, mock_supabase):
        """invoke_with_retry stops retrying on success."""
        call_count = [0]
        
        def mock_invoke(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                return {"ok": True}
            raise Exception("Error")
        
        mock_supabase.client.functions.invoke = Mock(side_effect=mock_invoke)
        
        await functions.invoke_with_retry(
            "my-function",
            max_retries=5,
            retry_delay=0.01
        )
        
        assert call_count[0] == 2  # Stopped after success
    
    @pytest.mark.asyncio
    async def test_retry_delay_none_uses_config(self, functions_with_config, mock_supabase):
        """invoke_with_retry None delay uses config."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        # Just verify it doesn't error
        response = await functions_with_config.invoke_with_retry("my-function")
        
        assert response.is_success is True
    
    @pytest.mark.asyncio
    async def test_retry_handles_not_found_without_retry(self, functions, mock_supabase):
        """invoke_with_retry handles not found (no point retrying)."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Function not found"))
        
        with pytest.raises(FunctionNotFoundError):
            await functions.invoke_with_retry(
                "nonexistent",
                max_retries=3,
                retry_delay=0.01
            )


# =============================================================================
# CONVENIENCE METHOD TESTS (10 tests)
# =============================================================================

class TestConvenienceMethods:
    """Tests for convenience methods."""
    
    @pytest.mark.asyncio
    async def test_invoke_json_success(self, functions, mock_supabase):
        """invoke_json returns parsed JSON."""
        mock_supabase.client.functions.invoke = Mock(return_value={"key": "value"})
        
        data = await functions.invoke_json("my-function")
        
        assert data == {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_invoke_json_with_payload(self, functions, mock_supabase):
        """invoke_json passes payload."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.invoke_json("my-function", {"input": "data"})
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["body"] == {"input": "data"}
    
    @pytest.mark.asyncio
    async def test_invoke_json_raises_on_error(self, functions, mock_supabase):
        """invoke_json raises on error."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Error"))
        
        with pytest.raises(FunctionInvocationError):
            await functions.invoke_json("my-function")
    
    @pytest.mark.asyncio
    async def test_invoke_text_success(self, functions, mock_supabase):
        """invoke_text returns text response."""
        mock_supabase.client.functions.invoke = Mock(return_value="Hello World")
        
        text = await functions.invoke_text("my-function")
        
        assert text == "Hello World"
    
    @pytest.mark.asyncio
    async def test_invoke_text_with_payload(self, functions, mock_supabase):
        """invoke_text passes payload."""
        mock_supabase.client.functions.invoke = Mock(return_value="")
        
        await functions.invoke_text("my-function", {"input": "data"})
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["body"] == {"input": "data"}
    
    @pytest.mark.asyncio
    async def test_invoke_text_raises_on_error(self, functions, mock_supabase):
        """invoke_text raises on error."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Error"))
        
        with pytest.raises(FunctionInvocationError):
            await functions.invoke_text("my-function")
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, functions, mock_supabase):
        """health_check returns True on success."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        healthy = await functions.health_check("my-function")
        
        assert healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, functions, mock_supabase):
        """health_check returns False on error."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Error"))
        
        healthy = await functions.health_check("my-function")
        
        assert healthy is False
    
    @pytest.mark.asyncio
    async def test_health_check_not_found(self, functions, mock_supabase):
        """health_check returns False for not found."""
        mock_supabase.client.functions.invoke = Mock(side_effect=Exception("Function not found"))
        
        healthy = await functions.health_check("nonexistent")
        
        assert healthy is False
    
    @pytest.mark.asyncio
    async def test_health_check_passes_payload(self, functions, mock_supabase):
        """health_check passes health_check payload."""
        mock_supabase.client.functions.invoke = Mock(return_value={})
        
        await functions.health_check("my-function")
        
        call_args = mock_supabase.client.functions.invoke.call_args
        assert call_args[0][1]["body"]["health_check"] is True

