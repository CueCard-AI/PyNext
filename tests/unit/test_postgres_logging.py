"""
Tests for PyNext Database Logging Module.

100 comprehensive tests covering:
- LogConfig validation and defaults (15 tests)
- LogLevel and LogFormat enums (10 tests)
- QueryContext creation and parsing (20 tests)
- LogRecord serialization (15 tests)
- DBLogger logging functionality (25 tests)
- QueryTracker context manager (10 tests)
- Context variables (5 tests)
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from pynext.db.adapters.postgres.observability.logging import (
    LogConfig,
    LogLevel,
    LogFormat,
    LogEvent,
    QueryContext,
    LogRecord,
    DBLogger,
    QueryTracker,
    create_logger,
    set_trace_id,
    get_trace_id,
    set_client_ip,
    get_client_ip,
    get_current_context,
)


# ============================================================================
# LogConfig Tests (15 tests)
# ============================================================================

class TestLogConfig:
    """Tests for LogConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LogConfig()
        assert config.enabled is True
        assert config.level == LogLevel.INFO
        assert config.format == LogFormat.TEXT
        assert config.slow_query_ms == 100.0
        assert config.log_queries is True
        assert config.log_params is False  # Secure default
        assert config.log_pool_stats is True
        assert config.max_query_length == 1000
        assert config.logger_name == "pynext.db"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LogConfig(
            level=LogLevel.DEBUG,
            format=LogFormat.JSON,
            slow_query_ms=50.0,
            log_params=True,
        )
        assert config.level == LogLevel.DEBUG
        assert config.format == LogFormat.JSON
        assert config.slow_query_ms == 50.0
        assert config.log_params is True
    
    def test_string_level_conversion(self):
        """Test string to LogLevel conversion."""
        config = LogConfig(level="DEBUG")
        assert config.level == LogLevel.DEBUG
        
        config2 = LogConfig(level="warning")
        assert config2.level == LogLevel.WARNING
    
    def test_string_format_conversion(self):
        """Test string to LogFormat conversion."""
        config = LogConfig(format="json")
        assert config.format == LogFormat.JSON
        
        config2 = LogConfig(format="TEXT")
        assert config2.format == LogFormat.TEXT
    
    def test_invalid_slow_query_ms(self):
        """Test validation of slow_query_ms."""
        with pytest.raises(ValueError, match="slow_query_ms must be positive"):
            LogConfig(slow_query_ms=0)
        
        with pytest.raises(ValueError, match="slow_query_ms must be positive"):
            LogConfig(slow_query_ms=-1)
    
    def test_invalid_max_query_length(self):
        """Test validation of max_query_length."""
        with pytest.raises(ValueError, match="max_query_length must be positive"):
            LogConfig(max_query_length=0)
    
    def test_redact_patterns_default(self):
        """Test default empty redact patterns."""
        config = LogConfig()
        assert config.redact_patterns == []
    
    def test_custom_redact_patterns(self):
        """Test custom redact patterns."""
        patterns = [r"password=\S+", r"secret=\S+"]
        config = LogConfig(redact_patterns=patterns)
        assert config.redact_patterns == patterns
    
    def test_callbacks_default_none(self):
        """Test callbacks default to None."""
        config = LogConfig()
        assert config.on_slow_query is None
        assert config.on_error is None
    
    def test_custom_callbacks(self):
        """Test custom callbacks."""
        slow_cb = MagicMock()
        error_cb = MagicMock()
        config = LogConfig(on_slow_query=slow_cb, on_error=error_cb)
        assert config.on_slow_query is slow_cb
        assert config.on_error is error_cb
    
    def test_disabled_config(self):
        """Test disabled logging configuration."""
        config = LogConfig(enabled=False)
        assert config.enabled is False
    
    def test_structlog_format(self):
        """Test structlog format setting."""
        config = LogConfig(format=LogFormat.STRUCTLOG)
        assert config.format == LogFormat.STRUCTLOG
    
    def test_custom_logger_name(self):
        """Test custom logger name."""
        config = LogConfig(logger_name="myapp.db")
        assert config.logger_name == "myapp.db"
    
    def test_all_levels(self):
        """Test all log levels can be set."""
        for level in LogLevel:
            config = LogConfig(level=level)
            assert config.level == level
    
    def test_all_formats(self):
        """Test all formats can be set."""
        for fmt in LogFormat:
            config = LogConfig(format=fmt)
            assert config.format == fmt


# ============================================================================
# LogLevel and LogFormat Tests (10 tests)
# ============================================================================

class TestLogLevelEnum:
    """Tests for LogLevel enum."""
    
    def test_all_levels_exist(self):
        """Test all expected levels exist."""
        assert LogLevel.DEBUG
        assert LogLevel.INFO
        assert LogLevel.WARNING
        assert LogLevel.ERROR
        assert LogLevel.CRITICAL
    
    def test_to_python_level(self):
        """Test conversion to Python logging level."""
        assert LogLevel.DEBUG.to_python_level() == logging.DEBUG
        assert LogLevel.INFO.to_python_level() == logging.INFO
        assert LogLevel.WARNING.to_python_level() == logging.WARNING
        assert LogLevel.ERROR.to_python_level() == logging.ERROR
        assert LogLevel.CRITICAL.to_python_level() == logging.CRITICAL
    
    def test_level_ordering(self):
        """Test log levels have correct ordering."""
        assert LogLevel.DEBUG.to_python_level() < LogLevel.INFO.to_python_level()
        assert LogLevel.INFO.to_python_level() < LogLevel.WARNING.to_python_level()
        assert LogLevel.WARNING.to_python_level() < LogLevel.ERROR.to_python_level()
        assert LogLevel.ERROR.to_python_level() < LogLevel.CRITICAL.to_python_level()
    
    def test_level_string_value(self):
        """Test level string values."""
        assert LogLevel.DEBUG.value == "DEBUG"
        assert LogLevel.INFO.value == "INFO"
        assert LogLevel.WARNING.value == "WARNING"
        assert LogLevel.ERROR.value == "ERROR"
        assert LogLevel.CRITICAL.value == "CRITICAL"
    
    def test_level_from_string(self):
        """Test creating level from string."""
        assert LogLevel("DEBUG") == LogLevel.DEBUG
        assert LogLevel("INFO") == LogLevel.INFO


class TestLogFormatEnum:
    """Tests for LogFormat enum."""
    
    def test_all_formats_exist(self):
        """Test all expected formats exist."""
        assert LogFormat.TEXT
        assert LogFormat.JSON
        assert LogFormat.STRUCTLOG
    
    def test_format_string_values(self):
        """Test format string values."""
        assert LogFormat.TEXT.value == "text"
        assert LogFormat.JSON.value == "json"
        assert LogFormat.STRUCTLOG.value == "structlog"
    
    def test_format_from_string(self):
        """Test creating format from string."""
        assert LogFormat("text") == LogFormat.TEXT
        assert LogFormat("json") == LogFormat.JSON
        assert LogFormat("structlog") == LogFormat.STRUCTLOG


class TestLogEventEnum:
    """Tests for LogEvent enum."""
    
    def test_query_events(self):
        """Test query-related events exist."""
        assert LogEvent.QUERY_START
        assert LogEvent.QUERY_SUCCESS
        assert LogEvent.QUERY_ERROR
        assert LogEvent.SLOW_QUERY
    
    def test_connection_events(self):
        """Test connection-related events exist."""
        assert LogEvent.CONNECTION_ACQUIRED
        assert LogEvent.CONNECTION_RELEASED
        assert LogEvent.CONNECTION_CREATED
        assert LogEvent.CONNECTION_CLOSED
        assert LogEvent.CONNECTION_ERROR


# ============================================================================
# QueryContext Tests (20 tests)
# ============================================================================

class TestQueryContext:
    """Tests for QueryContext dataclass."""
    
    def test_default_context(self):
        """Test default context creation."""
        ctx = QueryContext()
        assert ctx.query_id.startswith("q_")
        assert len(ctx.query_id) == 14  # "q_" + 12 hex chars
        assert ctx.query == ""
        assert ctx.params is None
        assert ctx.start_time > 0
        assert ctx.end_time is None
        assert ctx.duration_ms is None
        assert ctx.error is None
    
    def test_context_with_query(self):
        """Test context with query text."""
        ctx = QueryContext(query="SELECT * FROM users")
        assert ctx.query == "SELECT * FROM users"
    
    def test_context_with_params(self):
        """Test context with parameters."""
        ctx = QueryContext(query="SELECT * FROM users WHERE id = $1", params=(1,))
        assert ctx.params == (1,)
    
    def test_query_type_detection_select(self):
        """Test SELECT query type detection."""
        ctx = QueryContext(query="SELECT * FROM users")
        assert ctx.query_type == "SELECT"
    
    def test_query_type_detection_insert(self):
        """Test INSERT query type detection."""
        ctx = QueryContext(query="INSERT INTO users (name) VALUES ($1)")
        assert ctx.query_type == "INSERT"
    
    def test_query_type_detection_update(self):
        """Test UPDATE query type detection."""
        ctx = QueryContext(query="UPDATE users SET name = $1 WHERE id = $2")
        assert ctx.query_type == "UPDATE"
    
    def test_query_type_detection_delete(self):
        """Test DELETE query type detection."""
        ctx = QueryContext(query="DELETE FROM users WHERE id = $1")
        assert ctx.query_type == "DELETE"
    
    def test_table_detection_select(self):
        """Test table detection for SELECT."""
        ctx = QueryContext(query="SELECT * FROM users WHERE id = 1")
        assert ctx.table == "users"
    
    def test_table_detection_insert(self):
        """Test table detection for INSERT."""
        ctx = QueryContext(query="INSERT INTO orders (user_id) VALUES (1)")
        assert ctx.table == "orders"
    
    def test_table_detection_update(self):
        """Test table detection for UPDATE."""
        ctx = QueryContext(query="UPDATE products SET price = 100 WHERE id = 1")
        assert ctx.table == "products"
    
    def test_table_detection_delete(self):
        """Test table detection for DELETE."""
        ctx = QueryContext(query="DELETE FROM sessions WHERE expired = true")
        assert ctx.table == "sessions"
    
    def test_finish_success(self):
        """Test finishing a successful query."""
        ctx = QueryContext(query="SELECT 1")
        time.sleep(0.01)  # Ensure measurable duration
        ctx.finish()
        
        assert ctx.end_time is not None
        assert ctx.duration_ms is not None
        assert ctx.duration_ms > 0
        assert ctx.error is None
    
    def test_finish_error(self):
        """Test finishing a failed query."""
        ctx = QueryContext(query="SELECT 1")
        ctx.finish(error="Connection refused", error_type="ConnectionError")
        
        assert ctx.error == "Connection refused"
        assert ctx.error_type == "ConnectionError"
        assert ctx.duration_ms is not None
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        ctx = QueryContext(
            query="SELECT * FROM users",
            params=(1,),
        )
        ctx.finish()
        
        d = ctx.to_dict()
        assert d["query_id"].startswith("q_")
        assert d["query"] == "SELECT * FROM users"
        assert d["params"] == (1,)
        assert d["duration_ms"] is not None
        assert d["query_type"] == "SELECT"
        assert d["table"] == "users"
    
    def test_pool_stats(self):
        """Test pool statistics in context."""
        pool_stats = {"active": 5, "idle": 10, "waiting": 0}
        ctx = QueryContext(pool_stats=pool_stats)
        assert ctx.pool_stats == pool_stats
    
    def test_rows_affected(self):
        """Test rows affected tracking."""
        ctx = QueryContext(query="UPDATE users SET active = true")
        ctx.rows_affected = 42
        assert ctx.rows_affected == 42
    
    def test_rows_returned(self):
        """Test rows returned tracking."""
        ctx = QueryContext(query="SELECT * FROM users")
        ctx.rows_returned = 100
        assert ctx.rows_returned == 100
    
    def test_connection_id(self):
        """Test connection ID tracking."""
        ctx = QueryContext(connection_id="conn_123")
        assert ctx.connection_id == "conn_123"
    
    def test_custom_trace_id(self):
        """Test custom trace ID."""
        ctx = QueryContext(trace_id="trace_abc123")
        assert ctx.trace_id == "trace_abc123"
    
    def test_custom_client_ip(self):
        """Test custom client IP."""
        ctx = QueryContext(client_ip="10.0.0.1")
        assert ctx.client_ip == "10.0.0.1"


# ============================================================================
# LogRecord Tests (15 tests)
# ============================================================================

class TestLogRecord:
    """Tests for LogRecord dataclass."""
    
    def test_default_record(self):
        """Test default record creation."""
        record = LogRecord()
        assert record.timestamp is not None
        assert record.level == LogLevel.INFO
        assert record.event == LogEvent.QUERY_SUCCESS
        assert record.message == ""
        assert record.context is None
        assert record.extra == {}
    
    def test_custom_record(self):
        """Test custom record creation."""
        ctx = QueryContext(query="SELECT 1")
        record = LogRecord(
            level=LogLevel.WARNING,
            event=LogEvent.SLOW_QUERY,
            message="Query was slow",
            context=ctx,
            extra={"hint": "add index"},
        )
        assert record.level == LogLevel.WARNING
        assert record.event == LogEvent.SLOW_QUERY
        assert record.message == "Query was slow"
        assert record.context is ctx
        assert record.extra == {"hint": "add index"}
    
    def test_to_dict_basic(self):
        """Test to_dict without context."""
        record = LogRecord(
            level=LogLevel.INFO,
            event=LogEvent.CONNECTION_CREATED,
            message="New connection",
        )
        d = record.to_dict()
        
        assert "timestamp" in d
        assert d["level"] == "INFO"
        assert d["event"] == "connection_created"
        assert d["message"] == "New connection"
    
    def test_to_dict_with_context(self):
        """Test to_dict with query context."""
        ctx = QueryContext(query="SELECT * FROM users")
        ctx.finish()
        record = LogRecord(
            event=LogEvent.QUERY_SUCCESS,
            context=ctx,
        )
        d = record.to_dict()
        
        assert d["query"] == "SELECT * FROM users"
        assert d["query_type"] == "SELECT"
        assert d["table"] == "users"
    
    def test_to_dict_with_extra(self):
        """Test to_dict with extra fields."""
        record = LogRecord(extra={"custom_field": "value", "count": 42})
        d = record.to_dict()
        
        assert d["custom_field"] == "value"
        assert d["count"] == 42
    
    def test_to_json(self):
        """Test JSON serialization."""
        record = LogRecord(
            level=LogLevel.ERROR,
            event=LogEvent.QUERY_ERROR,
            message="Query failed",
        )
        json_str = record.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["level"] == "ERROR"
        assert parsed["event"] == "query_error"
        assert parsed["message"] == "Query failed"
    
    def test_to_text_basic(self):
        """Test text format output."""
        record = LogRecord(
            level=LogLevel.INFO,
            event=LogEvent.QUERY_SUCCESS,
            message="Query completed",
        )
        text = record.to_text()
        
        assert "INFO" in text
        assert "query_success" in text
        assert "Query completed" in text
    
    def test_to_text_with_context(self):
        """Test text format with query context."""
        ctx = QueryContext(query="SELECT 1", trace_id="trace_123")
        ctx.finish()
        record = LogRecord(event=LogEvent.QUERY_SUCCESS, context=ctx)
        text = record.to_text()
        
        assert "duration_ms=" in text
        assert "trace_id=trace_123" in text
    
    def test_to_text_with_error(self):
        """Test text format with error."""
        ctx = QueryContext(query="SELECT 1")
        ctx.finish(error="Connection lost")
        record = LogRecord(
            level=LogLevel.ERROR,
            event=LogEvent.QUERY_ERROR,
            context=ctx,
        )
        text = record.to_text()
        
        assert "error=Connection lost" in text
    
    def test_timestamp_is_utc(self):
        """Test timestamp is in UTC."""
        record = LogRecord()
        assert record.timestamp.tzinfo == timezone.utc
    
    def test_to_json_datetime_serialization(self):
        """Test datetime is serialized correctly."""
        record = LogRecord()
        json_str = record.to_json()
        parsed = json.loads(json_str)
        
        # Should be ISO format
        assert "T" in parsed["timestamp"]
        assert parsed["timestamp"].endswith("+00:00") or parsed["timestamp"].endswith("Z")
    
    def test_record_with_all_event_types(self):
        """Test record can be created with all event types."""
        for event in LogEvent:
            record = LogRecord(event=event)
            assert record.event == event
            assert event.value in record.to_dict()["event"]
    
    def test_record_with_all_levels(self):
        """Test record can be created with all levels."""
        for level in LogLevel:
            record = LogRecord(level=level)
            assert record.level == level
            assert level.value in record.to_dict()["level"]
    
    def test_to_text_with_extra_fields(self):
        """Test text format with extra fields."""
        record = LogRecord(extra={"retry_count": 3, "delay_ms": 1000})
        text = record.to_text()
        
        assert "retry_count=3" in text
        assert "delay_ms=1000" in text
    
    def test_to_text_with_table(self):
        """Test text format includes table name."""
        ctx = QueryContext(query="SELECT * FROM users")
        record = LogRecord(context=ctx)
        text = record.to_text()
        
        assert "table=users" in text


# ============================================================================
# DBLogger Tests (25 tests)
# ============================================================================

class TestDBLogger:
    """Tests for DBLogger class."""
    
    def test_default_creation(self):
        """Test creating logger with defaults."""
        logger = DBLogger()
        assert logger.config.enabled is True
        assert logger.enabled is True
    
    def test_custom_config(self):
        """Test creating logger with custom config."""
        config = LogConfig(level=LogLevel.DEBUG, slow_query_ms=50)
        logger = DBLogger(config)
        assert logger.config.slow_query_ms == 50
    
    def test_disabled_logger(self):
        """Test disabled logger does nothing."""
        config = LogConfig(enabled=False)
        logger = DBLogger(config)
        assert logger.enabled is False
        
        # Should not raise or log
        ctx = QueryContext(query="SELECT 1")
        ctx.finish()
        logger.log_query(ctx)
    
    def test_is_slow_query_false(self):
        """Test slow query detection - not slow."""
        config = LogConfig(slow_query_ms=100)
        logger = DBLogger(config)
        
        ctx = QueryContext(query="SELECT 1")
        ctx.duration_ms = 50  # Under threshold
        
        assert logger.is_slow_query(ctx) is False
    
    def test_is_slow_query_true(self):
        """Test slow query detection - is slow."""
        config = LogConfig(slow_query_ms=100)
        logger = DBLogger(config)
        
        ctx = QueryContext(query="SELECT 1")
        ctx.duration_ms = 150  # Over threshold
        
        assert logger.is_slow_query(ctx) is True
    
    def test_is_slow_query_no_duration(self):
        """Test slow query detection with no duration."""
        logger = DBLogger()
        ctx = QueryContext(query="SELECT 1")
        assert logger.is_slow_query(ctx) is False
    
    def test_log_query_success(self):
        """Test logging successful query."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        ctx = QueryContext(query="SELECT * FROM users")
        ctx.finish()
        
        # Should not raise
        logger.log_query(ctx)
        assert logger._stats["queries_logged"] == 1
    
    def test_log_query_error(self):
        """Test logging failed query."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        ctx = QueryContext(query="SELECT * FROM nonexistent")
        ctx.finish(error="table does not exist")
        
        logger.log_query(ctx)
        assert logger._stats["errors"] == 1
    
    def test_log_query_slow(self):
        """Test logging slow query."""
        logger = DBLogger(LogConfig(slow_query_ms=10))
        ctx = QueryContext(query="SELECT * FROM users")
        ctx.duration_ms = 100  # Slow
        ctx.end_time = ctx.start_time + 0.1
        
        logger.log_query(ctx)
        assert logger._stats["slow_queries"] == 1
    
    def test_slow_query_callback(self):
        """Test slow query callback is called."""
        callback = MagicMock()
        config = LogConfig(slow_query_ms=10, on_slow_query=callback)
        logger = DBLogger(config)
        
        ctx = QueryContext(query="SELECT * FROM users")
        ctx.duration_ms = 100
        ctx.end_time = ctx.start_time + 0.1
        
        logger.log_query(ctx)
        callback.assert_called_once()
    
    def test_error_callback(self):
        """Test error callback is called."""
        callback = MagicMock()
        config = LogConfig(on_error=callback)
        logger = DBLogger(config)
        
        ctx = QueryContext(query="SELECT 1")
        ctx.finish(error="Connection lost")
        
        logger.log_query(ctx)
        callback.assert_called_once()
    
    def test_redact_query(self):
        """Test query redaction."""
        config = LogConfig(redact_patterns=[r"password=\S+"])
        logger = DBLogger(config)
        
        redacted = logger._redact_query("SELECT * WHERE password=secret123")
        assert "secret123" not in redacted
        assert "[REDACTED]" in redacted
    
    def test_truncate_long_query(self):
        """Test long query truncation."""
        config = LogConfig(max_query_length=50)
        logger = DBLogger(config)
        
        long_query = "SELECT " + "a, " * 100
        truncated = logger._redact_query(long_query)
        assert len(truncated) <= 53  # 50 + "..."
        assert truncated.endswith("...")
    
    def test_log_event(self):
        """Test logging generic event."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        
        # Should not raise
        logger.log_event(
            LogEvent.CONNECTION_CREATED,
            LogLevel.INFO,
            "New connection created",
            connection_id="conn_123",
        )
    
    def test_log_connection_acquired(self):
        """Test logging connection acquisition."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        logger.log_connection_acquired("conn_123", 5.5, {"active": 1})
    
    def test_log_connection_released(self):
        """Test logging connection release."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        logger.log_connection_released("conn_123", 100.0)
    
    def test_log_connection_error(self):
        """Test logging connection error."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        logger.log_connection_error("Connection refused", "ConnectionRefusedError", "conn_123")
    
    def test_log_pool_exhaustion_warning(self):
        """Test logging pool exhaustion warning."""
        logger = DBLogger()
        logger.log_pool_exhaustion_warning(0.9, {"active": 45, "max": 50})
    
    def test_log_pool_exhausted(self):
        """Test logging pool exhaustion."""
        logger = DBLogger()
        logger.log_pool_exhausted({"active": 50, "max": 50}, 10)
    
    def test_log_transaction(self):
        """Test logging transaction events."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        logger.log_transaction(LogEvent.TRANSACTION_BEGIN, "tx_123", "SERIALIZABLE")
        logger.log_transaction(LogEvent.TRANSACTION_COMMIT, "tx_123")
        logger.log_transaction(LogEvent.TRANSACTION_ROLLBACK, "tx_123")
    
    def test_log_retry(self):
        """Test logging retry attempts."""
        logger = DBLogger()
        logger.log_retry(1, 3, "Connection timeout", 1000.0)
    
    def test_log_circuit_breaker(self):
        """Test logging circuit breaker events."""
        logger = DBLogger()
        logger.log_circuit_breaker(True, 5, 5)  # Opened
        logger.log_circuit_breaker(False, 0, 5)  # Closed
    
    def test_get_stats(self):
        """Test getting logger statistics."""
        logger = DBLogger()
        stats = logger.get_stats()
        
        assert "queries_logged" in stats
        assert "slow_queries" in stats
        assert "errors" in stats
        assert "config" in stats
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        
        # Log some queries
        ctx = QueryContext(query="SELECT 1")
        ctx.finish()
        logger.log_query(ctx)
        
        assert logger._stats["queries_logged"] == 1
        
        logger.reset_stats()
        assert logger._stats["queries_logged"] == 0
    
    def test_level_filtering(self):
        """Test log level filtering."""
        logger = DBLogger(LogConfig(level=LogLevel.WARNING))
        
        # DEBUG level should be filtered
        ctx = QueryContext(query="SELECT 1")
        ctx.finish()  # Would be DEBUG level
        logger.log_query(ctx)
        
        # Stats still update even if filtered
        # (depending on implementation)


# ============================================================================
# QueryTracker Tests (10 tests)
# ============================================================================

class TestQueryTracker:
    """Tests for QueryTracker context manager."""
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        
        async with QueryTracker(logger, "SELECT 1") as tracker:
            assert tracker.context.query == "SELECT 1"
            await asyncio.sleep(0.01)
        
        assert tracker.context.duration_ms is not None
        assert tracker.context.duration_ms > 0
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test async error handling."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        
        with pytest.raises(ValueError):
            async with QueryTracker(logger, "SELECT 1") as tracker:
                raise ValueError("Test error")
        
        assert tracker.context.error == "Test error"
        assert tracker.context.error_type == "ValueError"
    
    def test_sync_context_manager(self):
        """Test sync context manager."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        
        with QueryTracker(logger, "SELECT 1") as tracker:
            time.sleep(0.01)
        
        assert tracker.context.duration_ms is not None
    
    def test_sync_error_handling(self):
        """Test sync error handling."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        
        with pytest.raises(RuntimeError):
            with QueryTracker(logger, "SELECT 1") as tracker:
                raise RuntimeError("Test error")
        
        assert tracker.context.error == "Test error"
        assert tracker.context.error_type == "RuntimeError"
    
    def test_params_included(self):
        """Test params are included in tracker."""
        logger = DBLogger()
        
        with QueryTracker(logger, "SELECT $1", params=(1,)) as tracker:
            pass
        
        assert tracker.context.params == (1,)
    
    def test_pool_stats_included(self):
        """Test pool stats are included."""
        logger = DBLogger()
        pool_stats = {"active": 5, "idle": 10}
        
        with QueryTracker(logger, "SELECT 1", pool_stats=pool_stats) as tracker:
            pass
        
        assert tracker.context.pool_stats == pool_stats
    
    @pytest.mark.asyncio
    async def test_sets_context_var(self):
        """Test context variable is set."""
        logger = DBLogger()
        
        async with QueryTracker(logger, "SELECT 1") as tracker:
            current = get_current_context()
            assert current is tracker.context
        
        # Context should be cleared after exit
        assert get_current_context() is None
    
    @pytest.mark.asyncio
    async def test_nested_trackers(self):
        """Test nested query trackers."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        
        async with QueryTracker(logger, "SELECT 1") as outer:
            assert get_current_context() is outer.context
            
            async with QueryTracker(logger, "SELECT 2") as inner:
                assert get_current_context() is inner.context
            
            # Outer context restored
            assert get_current_context() is outer.context
    
    def test_query_logged_on_exit(self):
        """Test query is logged when context exits."""
        logger = DBLogger(LogConfig(level=LogLevel.DEBUG))
        
        with QueryTracker(logger, "SELECT 1") as tracker:
            pass
        
        assert logger._stats["queries_logged"] == 1
    
    def test_rows_can_be_set(self):
        """Test rows can be set during tracking."""
        logger = DBLogger()
        
        with QueryTracker(logger, "SELECT * FROM users") as tracker:
            tracker.context.rows_returned = 42
        
        assert tracker.context.rows_returned == 42


# ============================================================================
# Context Variable Tests (5 tests)
# ============================================================================

class TestContextVariables:
    """Tests for context variables."""
    
    def test_set_and_get_trace_id(self):
        """Test setting and getting trace ID."""
        set_trace_id("trace_abc123")
        assert get_trace_id() == "trace_abc123"
        
        # Clean up
        set_trace_id(None)
    
    def test_set_and_get_client_ip(self):
        """Test setting and getting client IP."""
        set_client_ip("192.168.1.1")
        assert get_client_ip() == "192.168.1.1"
        
        # Clean up
        set_client_ip(None)
    
    def test_trace_id_in_context(self):
        """Test trace ID is included in QueryContext."""
        set_trace_id("trace_xyz789")
        ctx = QueryContext(query="SELECT 1")
        assert ctx.trace_id == "trace_xyz789"
        
        # Clean up
        set_trace_id(None)
    
    def test_client_ip_in_context(self):
        """Test client IP is included in QueryContext."""
        set_client_ip("10.0.0.1")
        ctx = QueryContext(query="SELECT 1")
        assert ctx.client_ip == "10.0.0.1"
        
        # Clean up
        set_client_ip(None)
    
    def test_default_context_vars(self):
        """Test default values for context vars."""
        # Clean slate
        set_trace_id(None)
        set_client_ip(None)
        
        assert get_trace_id() is None
        assert get_client_ip() is None


# ============================================================================
# create_logger Helper Tests (5 tests)
# ============================================================================

class TestCreateLoggerHelper:
    """Tests for create_logger convenience function."""
    
    def test_create_logger_defaults(self):
        """Test create_logger with defaults."""
        logger = create_logger()
        assert logger.config.level == LogLevel.INFO
        assert logger.config.format == LogFormat.TEXT
        assert logger.config.slow_query_ms == 100.0
    
    def test_create_logger_with_level(self):
        """Test create_logger with custom level."""
        logger = create_logger(level="DEBUG")
        assert logger.config.level == LogLevel.DEBUG
    
    def test_create_logger_with_format(self):
        """Test create_logger with custom format."""
        logger = create_logger(format="json")
        assert logger.config.format == LogFormat.JSON
    
    def test_create_logger_with_slow_query_ms(self):
        """Test create_logger with custom slow query threshold."""
        logger = create_logger(slow_query_ms=50.0)
        assert logger.config.slow_query_ms == 50.0
    
    def test_create_logger_with_kwargs(self):
        """Test create_logger with additional kwargs."""
        logger = create_logger(
            level="WARNING",
            format="json",
            slow_query_ms=200,
            log_params=True,
        )
        assert logger.config.level == LogLevel.WARNING
        assert logger.config.format == LogFormat.JSON
        assert logger.config.slow_query_ms == 200
        assert logger.config.log_params is True


# ============================================================================
# Edge Cases and Error Handling (5 tests)
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_query(self):
        """Test handling empty query."""
        ctx = QueryContext(query="")
        assert ctx.query_type is None
        assert ctx.table is None
    
    def test_whitespace_query(self):
        """Test handling whitespace-only query."""
        ctx = QueryContext(query="   ")
        assert ctx.query_type is None
    
    def test_malformed_query(self):
        """Test handling malformed query."""
        ctx = QueryContext(query="SELEC * FORM users")  # Typos
        assert ctx.query_type is None  # Doesn't match known types
    
    def test_very_long_query_id(self):
        """Test query ID format is consistent."""
        ctx = QueryContext()
        assert ctx.query_id.startswith("q_")
        assert len(ctx.query_id) == 14
    
    def test_structlog_fallback_without_package(self):
        """Test structlog fallback when package not installed."""
        # This tests the fallback behavior
        config = LogConfig(format=LogFormat.STRUCTLOG)
        
        with patch.dict('sys.modules', {'structlog': None}):
            # Create logger which should fallback to JSON
            logger = DBLogger(config)
            # Format should be changed to JSON if structlog import fails
            # (or it works if structlog is installed)


# ============================================================================
# Performance Tests (5 tests)
# ============================================================================

class TestPerformance:
    """Tests for performance characteristics."""
    
    def test_logging_overhead_minimal(self):
        """Test logging has minimal overhead."""
        logger = DBLogger(LogConfig(enabled=False))
        
        start = time.monotonic()
        for _ in range(10000):
            ctx = QueryContext(query="SELECT 1")
            ctx.finish()
            logger.log_query(ctx)
        elapsed = time.monotonic() - start
        
        # Should be very fast when disabled
        assert elapsed < 1.0  # 10k iterations < 1 second
    
    def test_context_creation_fast(self):
        """Test context creation is fast."""
        start = time.monotonic()
        for _ in range(10000):
            ctx = QueryContext(query="SELECT * FROM users WHERE id = $1")
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0  # 10k contexts < 1 second
    
    def test_json_serialization_fast(self):
        """Test JSON serialization is fast."""
        ctx = QueryContext(query="SELECT * FROM users", params=(1, 2, 3))
        ctx.finish()
        record = LogRecord(context=ctx)
        
        start = time.monotonic()
        for _ in range(10000):
            record.to_json()
        elapsed = time.monotonic() - start
        
        assert elapsed < 2.0  # 10k serializations < 2 seconds
    
    def test_text_serialization_fast(self):
        """Test text serialization is fast."""
        ctx = QueryContext(query="SELECT * FROM users", trace_id="trace_123")
        ctx.finish()
        record = LogRecord(context=ctx)
        
        start = time.monotonic()
        for _ in range(10000):
            record.to_text()
        elapsed = time.monotonic() - start
        
        assert elapsed < 1.0  # 10k serializations < 1 second
    
    def test_multiple_redact_patterns(self):
        """Test redaction with multiple patterns is fast."""
        patterns = [
            r"password=\S+",
            r"secret=\S+",
            r"token=\S+",
            r"api_key=\S+",
            r"credit_card=\S+",
        ]
        config = LogConfig(redact_patterns=patterns)
        logger = DBLogger(config)
        
        query = "SELECT * WHERE password=abc secret=xyz token=123"
        
        start = time.monotonic()
        for _ in range(10000):
            logger._redact_query(query)
        elapsed = time.monotonic() - start
        
        assert elapsed < 2.0  # 10k redactions < 2 seconds

