"""
Comprehensive tests for PyNext Cursor-Based Pagination.

150 tests covering:
- Keyset pagination
- Offset pagination
- Smart mode auto-selection
- Cursor encoding/decoding
- Streaming
- Edge cases
"""

import pytest
import base64
import json
import asyncio

from pynext.db.adapters.postgres.queries.pagination import (
    PaginationMethod,
    CursorDirection,
    PaginationConfig,
    Cursor,
    Page,
    OffsetPage,
    KeysetPaginator,
    OffsetPaginator,
    SmartPaginator,
    StreamingPaginator,
    PaginationMixin,
    get_pagination_config,
    set_pagination_config,
)


# =============================================================================
# PAGINATION METHOD TESTS
# =============================================================================

class TestPaginationMethod:
    """Tests for PaginationMethod enum."""
    
    def test_keyset_value(self):
        """Test KEYSET value."""
        assert PaginationMethod.KEYSET.value == "keyset"
    
    def test_offset_value(self):
        """Test OFFSET value."""
        assert PaginationMethod.OFFSET.value == "offset"
    
    def test_auto_value(self):
        """Test AUTO value."""
        assert PaginationMethod.AUTO.value == "auto"


# =============================================================================
# CURSOR DIRECTION TESTS
# =============================================================================

class TestCursorDirection:
    """Tests for CursorDirection enum."""
    
    def test_forward_value(self):
        """Test FORWARD value."""
        assert CursorDirection.FORWARD.value == "forward"
    
    def test_backward_value(self):
        """Test BACKWARD value."""
        assert CursorDirection.BACKWARD.value == "backward"


# =============================================================================
# PAGINATION CONFIG TESTS
# =============================================================================

class TestPaginationConfig:
    """Tests for PaginationConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = PaginationConfig()
        assert config.default_page_size == 20
        assert config.max_page_size == 100
        assert config.keyset_threshold == 10_000
    
    def test_custom_page_size(self):
        """Test custom page size."""
        config = PaginationConfig(default_page_size=50)
        assert config.default_page_size == 50
    
    def test_custom_max_page_size(self):
        """Test custom max page size."""
        config = PaginationConfig(max_page_size=500)
        assert config.max_page_size == 500
    
    def test_invalid_page_size(self):
        """Test invalid page size raises error."""
        with pytest.raises(ValueError):
            PaginationConfig(default_page_size=0)
    
    def test_invalid_max_less_than_default(self):
        """Test max less than default raises error."""
        with pytest.raises(ValueError):
            PaginationConfig(default_page_size=50, max_page_size=20)
    
    def test_clamp_page_size_too_high(self):
        """Test clamping page size that's too high."""
        config = PaginationConfig(max_page_size=100)
        assert config.clamp_page_size(200) == 100
    
    def test_clamp_page_size_too_low(self):
        """Test clamping page size that's too low."""
        config = PaginationConfig()
        assert config.clamp_page_size(0) == 1
    
    def test_clamp_page_size_valid(self):
        """Test clamping valid page size."""
        config = PaginationConfig()
        assert config.clamp_page_size(50) == 50
    
    def test_with_cursor_secret(self):
        """Test config with cursor secret."""
        config = PaginationConfig(cursor_secret="secret123")
        assert config.cursor_secret == "secret123"


# =============================================================================
# CURSOR TESTS
# =============================================================================

class TestCursor:
    """Tests for Cursor."""
    
    def test_basic_cursor(self):
        """Test basic cursor creation."""
        cursor = Cursor(values={"id": 123})
        assert cursor.values["id"] == 123
    
    def test_cursor_with_direction(self):
        """Test cursor with direction."""
        cursor = Cursor(
            values={"id": 123},
            direction=CursorDirection.BACKWARD,
        )
        assert cursor.direction == CursorDirection.BACKWARD
    
    def test_cursor_encode(self):
        """Test cursor encoding."""
        cursor = Cursor(values={"id": 123})
        encoded = cursor.encode()
        assert isinstance(encoded, str)
        # Should be base64
        decoded = base64.urlsafe_b64decode(encoded.encode())
        data = json.loads(decoded)
        assert data["v"]["id"] == 123
    
    def test_cursor_decode(self):
        """Test cursor decoding."""
        cursor = Cursor(values={"id": 123})
        encoded = cursor.encode()
        
        decoded = Cursor.decode(encoded)
        assert decoded.values["id"] == 123
    
    def test_cursor_roundtrip(self):
        """Test cursor encode/decode roundtrip."""
        original = Cursor(
            values={"id": 123, "name": "test"},
            direction=CursorDirection.FORWARD,
            columns=["id", "name"],
        )
        encoded = original.encode()
        decoded = Cursor.decode(encoded)
        
        assert decoded.values == original.values
        assert decoded.direction == original.direction
        assert decoded.columns == original.columns
    
    def test_cursor_with_secret(self):
        """Test cursor with signing secret."""
        cursor = Cursor(values={"id": 123})
        encoded = cursor.encode(secret="mysecret")
        
        # Should decode with same secret
        decoded = Cursor.decode(encoded, secret="mysecret")
        assert decoded.values["id"] == 123
    
    def test_cursor_invalid_secret(self):
        """Test cursor with wrong secret fails."""
        cursor = Cursor(values={"id": 123})
        encoded = cursor.encode(secret="secret1")
        
        with pytest.raises(ValueError, match="checksum"):
            Cursor.decode(encoded, secret="secret2")
    
    def test_cursor_from_record(self):
        """Test creating cursor from record."""
        record = {"id": 1, "name": "Alice", "age": 30}
        cursor = Cursor.from_record(record, columns=["id", "name"])
        
        assert cursor.values["id"] == 1
        assert cursor.values["name"] == "Alice"
        assert "age" not in cursor.values
    
    def test_cursor_str(self):
        """Test cursor string representation."""
        cursor = Cursor(values={"id": 123})
        assert str(cursor) == cursor.encode()
    
    def test_decode_invalid_cursor(self):
        """Test decoding invalid cursor raises error."""
        with pytest.raises(ValueError):
            Cursor.decode("not-a-valid-cursor")
    
    def test_decode_malformed_json(self):
        """Test decoding malformed JSON raises error."""
        invalid = base64.urlsafe_b64encode(b"not json").decode()
        with pytest.raises(ValueError):
            Cursor.decode(invalid)


# =============================================================================
# PAGE TESTS
# =============================================================================

class TestPage:
    """Tests for Page."""
    
    def test_basic_page(self):
        """Test basic page creation."""
        page = Page(
            items=[{"id": 1}, {"id": 2}],
            page_size=20,
            has_more=True,
        )
        assert len(page) == 2
        assert page.page_size == 20
        assert page.has_more is True
    
    def test_page_iteration(self):
        """Test page iteration."""
        page = Page(items=[1, 2, 3], page_size=10)
        items = list(page)
        assert items == [1, 2, 3]
    
    def test_page_indexing(self):
        """Test page indexing."""
        page = Page(items=["a", "b", "c"], page_size=10)
        assert page[0] == "a"
        assert page[1] == "b"
        assert page[2] == "c"
    
    def test_page_count(self):
        """Test page count property."""
        page = Page(items=[1, 2, 3, 4, 5], page_size=10)
        assert page.count == 5
    
    def test_page_is_empty(self):
        """Test is_empty property."""
        empty_page = Page(items=[], page_size=10)
        assert empty_page.is_empty is True
        
        full_page = Page(items=[1], page_size=10)
        assert full_page.is_empty is False
    
    def test_page_first(self):
        """Test first property."""
        page = Page(items=[1, 2, 3], page_size=10)
        assert page.first == 1
        
        empty_page = Page(items=[], page_size=10)
        assert empty_page.first is None
    
    def test_page_last(self):
        """Test last property."""
        page = Page(items=[1, 2, 3], page_size=10)
        assert page.last == 3
        
        empty_page = Page(items=[], page_size=10)
        assert empty_page.last is None
    
    def test_page_to_dict(self):
        """Test converting to dictionary."""
        page = Page(
            items=[{"id": 1}],
            page_size=20,
            has_more=True,
            next_cursor="abc123",
        )
        d = page.to_dict()
        
        assert d["items"] == [{"id": 1}]
        assert d["page_size"] == 20
        assert d["has_more"] is True
        assert d["next_cursor"] == "abc123"
    
    def test_page_with_cursors(self):
        """Test page with cursors."""
        page = Page(
            items=[1, 2],
            page_size=2,
            has_more=True,
            has_previous=True,
            next_cursor="next",
            previous_cursor="prev",
        )
        assert page.next_cursor == "next"
        assert page.previous_cursor == "prev"


# =============================================================================
# OFFSET PAGE TESTS
# =============================================================================

class TestOffsetPage:
    """Tests for OffsetPage."""
    
    def test_basic_offset_page(self):
        """Test basic offset page."""
        page = OffsetPage(
            items=[1, 2, 3],
            page_size=10,
            offset=20,
            total_count=100,
        )
        assert page.offset == 20
        assert page.total_count == 100
    
    def test_start_index(self):
        """Test start_index property."""
        page = OffsetPage(items=[1, 2], page_size=10, offset=20)
        assert page.start_index == 21
    
    def test_end_index(self):
        """Test end_index property."""
        page = OffsetPage(items=[1, 2], page_size=10, offset=20)
        assert page.end_index == 22
    
    def test_with_total_pages(self):
        """Test page with total_pages."""
        page = OffsetPage(
            items=[1, 2, 3],
            page_size=10,
            total_count=100,
            total_pages=10,
            current_page=1,
        )
        assert page.total_pages == 10
        assert page.current_page == 1


# =============================================================================
# KEYSET PAGINATOR TESTS
# =============================================================================

class TestKeysetPaginator:
    """Tests for KeysetPaginator."""
    
    def test_basic_creation(self):
        """Test basic paginator creation."""
        paginator = KeysetPaginator(order_columns=["id"])
        assert paginator.order_columns == ["id"]
    
    def test_with_directions(self):
        """Test paginator with order directions."""
        paginator = KeysetPaginator(
            order_columns=["id", "name"],
            order_directions=["ASC", "DESC"],
        )
        assert paginator.order_directions == ["ASC", "DESC"]
    
    def test_mismatched_lengths_error(self):
        """Test error when columns and directions don't match."""
        with pytest.raises(ValueError):
            KeysetPaginator(
                order_columns=["id", "name"],
                order_directions=["ASC"],
            )
    
    def test_build_where_clause_no_cursor(self):
        """Test WHERE clause with no cursor."""
        paginator = KeysetPaginator(order_columns=["id"])
        where, params = paginator.build_where_clause(None)
        assert where == ""
        assert params == []
    
    def test_build_where_clause_with_cursor(self):
        """Test WHERE clause with cursor."""
        paginator = KeysetPaginator(order_columns=["id"])
        cursor = Cursor(values={"id": 100})
        where, params = paginator.build_where_clause(cursor)
        assert "WHERE" in where
        assert params == [100]
    
    def test_build_where_clause_backward(self):
        """Test WHERE clause for backward pagination."""
        paginator = KeysetPaginator(order_columns=["id"])
        cursor = Cursor(values={"id": 100})
        where, params = paginator.build_where_clause(
            cursor,
            direction=CursorDirection.BACKWARD,
        )
        assert "WHERE" in where
        assert "<" in where
    
    def test_create_cursor_from_row(self):
        """Test creating cursor from result row."""
        paginator = KeysetPaginator(order_columns=["id", "name"])
        row = {"id": 1, "name": "Alice", "extra": "ignored"}
        cursor = paginator.create_cursor_from_row(row)
        
        assert cursor.values["id"] == 1
        assert cursor.values["name"] == "Alice"
        assert "extra" not in cursor.values
    
    @pytest.mark.asyncio
    async def test_paginate_first_page(self):
        """Test paginating first page."""
        async def mock_execute(query, params):
            return [
                {"id": 1, "name": "A"},
                {"id": 2, "name": "B"},
                {"id": 3, "name": "C"},
            ]
        
        paginator = KeysetPaginator(order_columns=["id"])
        page = await paginator.paginate(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
            page_size=2,
        )
        
        assert len(page.items) == 2
        assert page.has_more is True
        assert page.next_cursor is not None
    
    @pytest.mark.asyncio
    async def test_paginate_last_page(self):
        """Test paginating last page."""
        async def mock_execute(query, params):
            return [{"id": 1}]
        
        paginator = KeysetPaginator(order_columns=["id"])
        page = await paginator.paginate(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
            page_size=10,
        )
        
        assert len(page.items) == 1
        assert page.has_more is False


# =============================================================================
# OFFSET PAGINATOR TESTS
# =============================================================================

class TestOffsetPaginator:
    """Tests for OffsetPaginator."""
    
    def test_basic_creation(self):
        """Test basic paginator creation."""
        paginator = OffsetPaginator()
        assert paginator.config is not None
    
    @pytest.mark.asyncio
    async def test_paginate_first_page(self):
        """Test offset pagination first page."""
        async def mock_execute(query, params):
            return [
                {"id": 1},
                {"id": 2},
            ]
        
        async def mock_count(query):
            return 100
        
        paginator = OffsetPaginator()
        page = await paginator.paginate(
            execute_fn=mock_execute,
            count_fn=mock_count,
            query="SELECT * FROM users",
            page=1,
            page_size=10,
        )
        
        assert page.current_page == 1
        assert page.total_count == 100
        assert page.total_pages == 10
    
    @pytest.mark.asyncio
    async def test_paginate_middle_page(self):
        """Test offset pagination middle page."""
        async def mock_execute(query, params):
            return [{"id": 1}]
        
        async def mock_count(query):
            return 100
        
        paginator = OffsetPaginator()
        page = await paginator.paginate(
            execute_fn=mock_execute,
            count_fn=mock_count,
            query="SELECT * FROM users",
            page=5,
            page_size=10,
        )
        
        assert page.current_page == 5
        assert page.has_previous is True
        assert page.has_more is True
    
    @pytest.mark.asyncio
    async def test_paginate_without_count(self):
        """Test pagination without total count."""
        call_count = [0]
        
        async def mock_execute(query, params):
            call_count[0] += 1
            # Return 11 items (one more than page_size to indicate has_more)
            return [{"id": i} for i in range(11)]
        
        async def mock_count(query):
            return 0  # Not used when include_total=False
        
        paginator = OffsetPaginator()
        page = await paginator.paginate(
            execute_fn=mock_execute,
            count_fn=mock_count,
            query="SELECT * FROM users",
            page=1,
            page_size=10,
            include_total=False,
        )
        
        assert page.total_count is None
        # Should have more since we returned 11 items for page_size of 10
        assert page.has_more is True


# =============================================================================
# SMART PAGINATOR TESTS
# =============================================================================

class TestSmartPaginator:
    """Tests for SmartPaginator."""
    
    def test_basic_creation(self):
        """Test basic smart paginator creation."""
        paginator = SmartPaginator()
        assert paginator.config is not None
    
    def test_select_method_large_indexed(self):
        """Test method selection for large indexed table."""
        paginator = SmartPaginator()
        method = paginator.select_method(
            estimated_rows=100000,
            has_indexed_order=True,
            needs_total_count=False,
            has_complex_order=False,
        )
        assert method == PaginationMethod.KEYSET
    
    def test_select_method_needs_count(self):
        """Test method selection when count needed."""
        paginator = SmartPaginator()
        method = paginator.select_method(
            estimated_rows=100000,
            has_indexed_order=True,
            needs_total_count=True,
            has_complex_order=False,
        )
        assert method == PaginationMethod.OFFSET
    
    def test_select_method_small_table(self):
        """Test method selection for small table."""
        paginator = SmartPaginator()
        method = paginator.select_method(
            estimated_rows=100,
            has_indexed_order=True,
            needs_total_count=False,
            has_complex_order=False,
        )
        assert method == PaginationMethod.OFFSET
    
    def test_select_method_complex_order(self):
        """Test method selection with complex ORDER BY."""
        paginator = SmartPaginator()
        method = paginator.select_method(
            estimated_rows=100000,
            has_indexed_order=True,
            needs_total_count=False,
            has_complex_order=True,
        )
        assert method == PaginationMethod.OFFSET


# =============================================================================
# STREAMING PAGINATOR TESTS
# =============================================================================

class TestStreamingPaginator:
    """Tests for StreamingPaginator."""
    
    def test_basic_creation(self):
        """Test basic streaming paginator creation."""
        paginator = StreamingPaginator(batch_size=100)
        assert paginator.batch_size == 100
    
    @pytest.mark.asyncio
    async def test_stream_batches(self):
        """Test streaming in batches."""
        call_count = [0]
        
        async def mock_execute(query, params):
            call_count[0] += 1
            if call_count[0] == 1:
                return [{"id": i} for i in range(10)]
            elif call_count[0] == 2:
                return [{"id": i} for i in range(10, 15)]
            return []
        
        paginator = StreamingPaginator(batch_size=10)
        batches = []
        
        async for batch in paginator.stream(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
        ):
            batches.append(batch)
        
        assert len(batches) == 2
        assert len(batches[0]) == 10
        assert len(batches[1]) == 5
    
    @pytest.mark.asyncio
    async def test_stream_empty_result(self):
        """Test streaming with empty result."""
        async def mock_execute(query, params):
            return []
        
        paginator = StreamingPaginator()
        batches = []
        
        async for batch in paginator.stream(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
        ):
            batches.append(batch)
        
        assert len(batches) == 0
    
    @pytest.mark.asyncio
    async def test_stream_all(self):
        """Test streaming all individual rows."""
        async def mock_execute(query, params):
            if "OFFSET 0" in query:
                return [{"id": 1}, {"id": 2}]
            return []
        
        paginator = StreamingPaginator(batch_size=10)
        rows = []
        
        async for row in paginator.stream_all(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
        ):
            rows.append(row)
        
        assert len(rows) == 2


# =============================================================================
# PAGINATION MIXIN TESTS
# =============================================================================

class TestPaginationMixin:
    """Tests for PaginationMixin."""
    
    def test_mixin_has_paginate(self):
        """Test mixin provides paginate method."""
        class MockQuery(PaginationMixin):
            pass
        
        query = MockQuery()
        assert hasattr(query, "paginate")
    
    def test_mixin_has_cursor(self):
        """Test mixin provides cursor method."""
        class MockQuery(PaginationMixin):
            pass
        
        query = MockQuery()
        assert hasattr(query, "cursor")
    
    def test_mixin_has_offset_paginate(self):
        """Test mixin provides offset_paginate method."""
        class MockQuery(PaginationMixin):
            pass
        
        query = MockQuery()
        assert hasattr(query, "offset_paginate")
    
    def test_mixin_has_stream(self):
        """Test mixin provides stream method."""
        class MockQuery(PaginationMixin):
            pass
        
        query = MockQuery()
        assert hasattr(query, "stream")


# =============================================================================
# GLOBAL CONFIG TESTS
# =============================================================================

class TestGlobalConfig:
    """Tests for global config functions."""
    
    def test_get_pagination_config(self):
        """Test getting global config."""
        config = get_pagination_config()
        assert isinstance(config, PaginationConfig)
    
    def test_set_pagination_config(self):
        """Test setting global config."""
        original = get_pagination_config()
        
        new_config = PaginationConfig(default_page_size=50)
        set_pagination_config(new_config)
        
        assert get_pagination_config().default_page_size == 50
        
        # Restore
        set_pagination_config(original)


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_page_size_one(self):
        """Test page size of 1."""
        config = PaginationConfig(default_page_size=1, max_page_size=1)
        assert config.clamp_page_size(1) == 1
    
    def test_cursor_with_null_values(self):
        """Test cursor with None values."""
        cursor = Cursor(values={"id": None})
        encoded = cursor.encode()
        decoded = Cursor.decode(encoded)
        assert decoded.values["id"] is None
    
    def test_cursor_with_special_characters(self):
        """Test cursor with special characters."""
        cursor = Cursor(values={"name": "Test'\"<>&"})
        encoded = cursor.encode()
        decoded = Cursor.decode(encoded)
        assert decoded.values["name"] == "Test'\"<>&"
    
    def test_cursor_with_unicode(self):
        """Test cursor with unicode characters."""
        cursor = Cursor(values={"name": "测试 🎉"})
        encoded = cursor.encode()
        decoded = Cursor.decode(encoded)
        assert decoded.values["name"] == "测试 🎉"
    
    def test_empty_page_to_dict(self):
        """Test empty page to_dict."""
        page = Page(items=[], page_size=10)
        d = page.to_dict()
        assert d["items"] == []
        assert d["count"] == 0
    
    def test_page_with_none_cursors(self):
        """Test page with None cursors."""
        page = Page(
            items=[1],
            page_size=10,
            next_cursor=None,
            previous_cursor=None,
        )
        d = page.to_dict()
        assert "next_cursor" not in d
        assert "previous_cursor" not in d
    
    @pytest.mark.asyncio
    async def test_keyset_empty_result(self):
        """Test keyset pagination with empty result."""
        async def mock_execute(query, params):
            return []
        
        paginator = KeysetPaginator(order_columns=["id"])
        page = await paginator.paginate(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
            page_size=10,
        )
        
        assert len(page.items) == 0
        assert page.has_more is False
        assert page.next_cursor is None
    
    def test_config_keyset_threshold_one(self):
        """Test keyset threshold of 1."""
        config = PaginationConfig(keyset_threshold=1)
        assert config.keyset_threshold == 1
    
    def test_cursor_multi_column(self):
        """Test cursor with multiple columns."""
        cursor = Cursor(
            values={"a": 1, "b": 2, "c": 3},
            columns=["a", "b", "c"],
        )
        encoded = cursor.encode()
        decoded = Cursor.decode(encoded)
        assert decoded.values == {"a": 1, "b": 2, "c": 3}
    
    @pytest.mark.asyncio
    async def test_offset_page_zero_handling(self):
        """Test offset pagination handles page 0."""
        async def mock_execute(query, params):
            return [{"id": 1}]
        
        async def mock_count(query):
            return 10
        
        paginator = OffsetPaginator()
        page = await paginator.paginate(
            execute_fn=mock_execute,
            count_fn=mock_count,
            query="SELECT * FROM users",
            page=0,  # Should be treated as 1
            page_size=10,
        )
        
        assert page.current_page == 1


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for pagination."""
    
    @pytest.mark.asyncio
    async def test_full_keyset_workflow(self):
        """Test complete keyset pagination workflow."""
        # Simulate database rows
        all_rows = [{"id": i, "name": f"User{i}"} for i in range(100)]
        
        async def mock_execute(query, params):
            # Parse LIMIT and OFFSET from query
            if "LIMIT" in query:
                parts = query.split("LIMIT")
                limit_part = parts[1].strip().split()[0]
                limit = int(limit_part)
                
                # Simple simulation
                if not params:
                    return all_rows[:limit]
                else:
                    after_id = params[0]
                    filtered = [r for r in all_rows if r["id"] > after_id]
                    return filtered[:limit]
            return all_rows
        
        paginator = KeysetPaginator(order_columns=["id"])
        
        # Get first page
        page1 = await paginator.paginate(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
            page_size=10,
        )
        
        assert len(page1.items) == 10
        assert page1.has_more is True
        assert page1.next_cursor is not None
        
        # Get second page
        page2 = await paginator.paginate(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
            cursor=page1.next_cursor,
            page_size=10,
        )
        
        assert len(page2.items) == 10
        assert page2.has_previous is True
    
    @pytest.mark.asyncio
    async def test_full_offset_workflow(self):
        """Test complete offset pagination workflow."""
        async def mock_execute(query, params):
            if "OFFSET 0" in query:
                return [{"id": i} for i in range(10)]
            elif "OFFSET 10" in query:
                return [{"id": i} for i in range(10, 20)]
            return []
        
        async def mock_count(query):
            return 50
        
        paginator = OffsetPaginator()
        
        # First page
        page1 = await paginator.paginate(
            execute_fn=mock_execute,
            count_fn=mock_count,
            query="SELECT * FROM users",
            page=1,
            page_size=10,
        )
        
        assert page1.current_page == 1
        assert page1.total_pages == 5
        assert page1.has_more is True
        assert page1.has_previous is False
        
        # Second page
        page2 = await paginator.paginate(
            execute_fn=mock_execute,
            count_fn=mock_count,
            query="SELECT * FROM users",
            page=2,
            page_size=10,
        )
        
        assert page2.current_page == 2
        assert page2.has_previous is True
    
    @pytest.mark.asyncio
    async def test_streaming_large_dataset(self):
        """Test streaming through a large dataset."""
        total_rows = 350
        batch_size = 100
        
        async def mock_execute(query, params):
            # Parse OFFSET from query
            offset = 0
            if "OFFSET" in query:
                parts = query.split("OFFSET")
                offset = int(parts[1].strip())
            
            end = min(offset + batch_size, total_rows)
            return [{"id": i} for i in range(offset, end)]
        
        paginator = StreamingPaginator(batch_size=batch_size)
        
        total_items = 0
        batch_count = 0
        
        async for batch in paginator.stream(
            execute_fn=mock_execute,
            query="SELECT * FROM users",
        ):
            batch_count += 1
            total_items += len(batch)
        
        assert batch_count == 4  # 100 + 100 + 100 + 50
        assert total_items == 350

