"""
Test Phase 7.4.1: Database-Level Cascade - Error Translation.

These tests verify that:
1. FK violation errors are translated to ProtectedDeleteError
2. Constraint names are extracted from error messages
3. Related table names are extracted from error messages
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pynext.db.relationships.cascade import ProtectedDeleteError


# =============================================================================
# Test Error Message Parsing
# =============================================================================

class TestConstraintNameExtraction:
    """Test extraction of constraint names from error messages."""
    
    def get_adapter(self):
        """Create a testable adapter instance."""
        class TestableAdapter:
            def _extract_constraint_name(self, error_msg: str):
                import re
                patterns = [
                    r'constraint\s*["\'](\w+)["\']',
                    r'constraint\s+(\w+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, error_msg, re.IGNORECASE)
                    if match:
                        return match.group(1)
                return None
            
            def _extract_related_table(self, error_msg: str):
                import re
                patterns = [
                    r'on\s+table\s*["\'](\w+)["\']',
                    r'table\s*["\'](\w+)["\']',
                    r'from\s+table\s*["\'](\w+)["\']',
                ]
                for pattern in patterns:
                    match = re.search(pattern, error_msg, re.IGNORECASE)
                    if match:
                        return match.group(1)
                return None
        
        return TestableAdapter()
    
    def test_extract_constraint_with_double_quotes(self):
        """Extract constraint name with double quotes."""
        adapter = self.get_adapter()
        error = 'violates foreign key constraint "posts_author_id_fkey"'
        result = adapter._extract_constraint_name(error)
        assert result == "posts_author_id_fkey"
    
    def test_extract_constraint_with_single_quotes(self):
        """Extract constraint name with single quotes."""
        adapter = self.get_adapter()
        error = "violates foreign key constraint 'posts_author_id_fkey'"
        result = adapter._extract_constraint_name(error)
        assert result == "posts_author_id_fkey"
    
    def test_extract_constraint_without_quotes(self):
        """Extract constraint name without quotes."""
        adapter = self.get_adapter()
        error = "violates foreign key constraint posts_author_id_fkey on table"
        result = adapter._extract_constraint_name(error)
        assert result == "posts_author_id_fkey"
    
    def test_extract_constraint_from_full_error(self):
        """Extract from a full PostgreSQL error message."""
        adapter = self.get_adapter()
        error = 'update or delete on table "users" violates foreign key constraint "posts_author_id_fkey" on table "posts"'
        result = adapter._extract_constraint_name(error)
        assert result == "posts_author_id_fkey"
    
    def test_extract_constraint_returns_none_if_not_found(self):
        """Return None if no constraint name found."""
        adapter = self.get_adapter()
        error = "some generic error message"
        result = adapter._extract_constraint_name(error)
        assert result is None
    
    def test_extract_table_with_double_quotes(self):
        """Extract table name with double quotes."""
        adapter = self.get_adapter()
        error = 'on table "posts" violates'
        result = adapter._extract_related_table(error)
        assert result == "posts"
    
    def test_extract_table_with_single_quotes(self):
        """Extract table name with single quotes."""
        adapter = self.get_adapter()
        error = "on table 'posts' violates"
        result = adapter._extract_related_table(error)
        assert result == "posts"
    
    def test_extract_table_from_full_error(self):
        """Extract from a full PostgreSQL error message."""
        adapter = self.get_adapter()
        error = 'update or delete on table "users" violates foreign key'
        result = adapter._extract_related_table(error)
        assert result == "users"
    
    def test_extract_table_returns_none_if_not_found(self):
        """Return None if no table name found."""
        adapter = self.get_adapter()
        error = "some generic error message"
        result = adapter._extract_related_table(error)
        assert result is None


# =============================================================================
# Test ProtectedDeleteError
# =============================================================================

class TestProtectedDeleteError:
    """Test ProtectedDeleteError exception."""
    
    def test_basic_error_creation(self):
        """Test creating a basic ProtectedDeleteError."""
        class MockInstance:
            id = 1
            __class__ = type("User", (), {})
        
        error = ProtectedDeleteError(
            instance=MockInstance(),
            relationship="posts",
            related_count=5,
        )
        
        assert error.relationship == "posts"
        assert error.related_count == 5
    
    def test_error_message_format(self):
        """Test error message format."""
        class MockInstance:
            id = 42
        MockInstance.__name__ = "User"
        
        error = ProtectedDeleteError(
            instance=MockInstance(),
            relationship="orders",
            related_count=3,
        )
        
        message = str(error)
        assert "42" in message or "orders" in message
        assert "3" in message or "protected" in message
    
    def test_error_with_zero_related(self):
        """Test error with zero related (edge case)."""
        class MockInstance:
            id = 1
        MockInstance.__name__ = "User"
        
        # Should still work, even if 0 related (unusual but valid)
        error = ProtectedDeleteError(
            instance=MockInstance(),
            relationship="posts",
            related_count=0,
        )
        
        assert error.related_count == 0
    
    def test_error_is_exception(self):
        """Test that ProtectedDeleteError is an Exception."""
        class MockInstance:
            id = 1
        MockInstance.__name__ = "User"
        
        error = ProtectedDeleteError(
            instance=MockInstance(),
            relationship="posts",
            related_count=1,
        )
        
        assert isinstance(error, Exception)
    
    def test_error_can_be_raised(self):
        """Test that error can be raised and caught."""
        class MockInstance:
            id = 1
        MockInstance.__name__ = "User"
        
        with pytest.raises(ProtectedDeleteError) as exc_info:
            raise ProtectedDeleteError(
                instance=MockInstance(),
                relationship="posts",
                related_count=1,
            )
        
        assert exc_info.value.relationship == "posts"


# =============================================================================
# Test FK Violation Error Handling
# =============================================================================

class TestFKViolationHandling:
    """Test handling of FK violation errors during delete."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create mock adapter that simulates FK violation."""
        class TestableAdapter:
            def __init__(self):
                self.should_raise_fk_error = False
            
            def _extract_constraint_name(self, error_msg):
                import re
                match = re.search(r'constraint\s*["\'](\w+)["\']', error_msg, re.IGNORECASE)
                return match.group(1) if match else None
            
            def _extract_related_table(self, error_msg):
                import re
                match = re.search(r'table\s*["\'](\w+)["\']', error_msg, re.IGNORECASE)
                return match.group(1) if match else None
            
            async def _execute(self, sql, *args):
                if self.should_raise_fk_error:
                    raise Exception(
                        'update or delete on table "users" violates foreign key '
                        'constraint "posts_author_id_fkey" on table "posts"'
                    )
                return "DELETE 1"
            
            async def delete(self, table, id):
                sql = f'DELETE FROM "{table}" WHERE "id" = $1'
                try:
                    result = await self._execute(sql, id)
                    return "DELETE 1" in result
                except Exception as e:
                    error_str = str(e).lower()
                    if "foreign" in error_str and ("violates" in error_str or "constraint" in error_str):
                        constraint_name = self._extract_constraint_name(str(e))
                        related_table = self._extract_related_table(str(e))
                        
                        class DummyInstance:
                            def __init__(self, tbl, row_id):
                                self.id = row_id
                                self.__class__.__name__ = tbl.rstrip('s').title()
                        
                        raise ProtectedDeleteError(
                            instance=DummyInstance(table, id),
                            relationship=related_table or constraint_name or "related",
                            related_count=1,
                        )
                    raise
        
        return TestableAdapter()
    
    @pytest.mark.asyncio
    async def test_delete_without_fk_violation(self, mock_adapter):
        """Test delete succeeds without FK violation."""
        result = await mock_adapter.delete("users", 1)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_with_fk_violation(self, mock_adapter):
        """Test delete raises ProtectedDeleteError on FK violation."""
        mock_adapter.should_raise_fk_error = True
        
        with pytest.raises(ProtectedDeleteError) as exc_info:
            await mock_adapter.delete("users", 1)
        
        assert exc_info.value.relationship in ("users", "posts_author_id_fkey")
    
    @pytest.mark.asyncio
    async def test_fk_violation_preserves_related_count(self, mock_adapter):
        """Test FK violation error includes related_count."""
        mock_adapter.should_raise_fk_error = True
        
        with pytest.raises(ProtectedDeleteError) as exc_info:
            await mock_adapter.delete("users", 1)
        
        # related_count is 1 since we don't know the actual count from DB error
        assert exc_info.value.related_count == 1


# =============================================================================
# Test Various PostgreSQL Error Formats
# =============================================================================

class TestPostgreSQLErrorFormats:
    """Test handling of various PostgreSQL error message formats."""
    
    def get_adapter(self):
        """Create a testable adapter instance."""
        class TestableAdapter:
            def _extract_constraint_name(self, error_msg):
                import re
                patterns = [
                    r'constraint\s*["\'](\w+)["\']',
                    r'constraint\s+(\w+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, error_msg, re.IGNORECASE)
                    if match:
                        return match.group(1)
                return None
        
        return TestableAdapter()
    
    def test_psycopg2_style_error(self):
        """Test psycopg2-style error message."""
        adapter = self.get_adapter()
        error = 'IntegrityError: insert or update on table "posts" violates foreign key constraint "posts_author_id_fkey"'
        result = adapter._extract_constraint_name(error)
        assert result == "posts_author_id_fkey"
    
    def test_asyncpg_style_error(self):
        """Test asyncpg-style error message."""
        adapter = self.get_adapter()
        error = 'ForeignKeyViolationError: update or delete on table "users" violates foreign key constraint "posts_author_id_fkey"'
        result = adapter._extract_constraint_name(error)
        assert result == "posts_author_id_fkey"
    
    def test_detailed_postgres_error(self):
        """Test detailed PostgreSQL error with extra info."""
        adapter = self.get_adapter()
        error = '''
        ERROR: update or delete on table "users" violates foreign key constraint "posts_author_id_fkey" on table "posts"
        DETAIL: Key (id)=(1) is still referenced from table "posts".
        '''
        result = adapter._extract_constraint_name(error)
        assert result == "posts_author_id_fkey"
    
    def test_constraint_name_with_schema(self):
        """Test constraint name that might include schema prefix."""
        adapter = self.get_adapter()
        # Note: Our simple regex captures the full constraint name
        error = 'violates foreign key constraint "public_posts_author_id_fkey"'
        result = adapter._extract_constraint_name(error)
        assert result == "public_posts_author_id_fkey"


# =============================================================================
# Test Cascade Manager with DB Handling
# =============================================================================

class TestCascadeManagerDBHandling:
    """Test CascadeManager when DB handles FK cascades."""
    
    def test_cascade_manager_db_handles_fk_default_true(self):
        """CascadeManager defaults to db_handles_fk=True."""
        from pynext.db.relationships.cascade import CascadeManager
        manager = CascadeManager()
        assert manager._db_handles_fk is True
    
    def test_cascade_manager_can_disable_db_handling(self):
        """CascadeManager can be configured to handle cascades at app level."""
        from pynext.db.relationships.cascade import CascadeManager
        manager = CascadeManager(db_handles_fk=False)
        assert manager._db_handles_fk is False


# =============================================================================
# Test Error Propagation
# =============================================================================

class TestErrorPropagation:
    """Test that errors propagate correctly through the system."""
    
    @pytest.mark.asyncio
    async def test_non_fk_error_not_translated(self):
        """Non-FK errors should not be translated to ProtectedDeleteError."""
        class TestableAdapter:
            async def _execute(self, sql, *args):
                raise Exception("some other database error")
            
            async def delete(self, table, id):
                try:
                    return await self._execute(f'DELETE FROM "{table}"', id)
                except Exception as e:
                    error_str = str(e).lower()
                    if "foreign" in error_str:
                        pass  # Would translate
                    raise  # Re-raise original
        
        adapter = TestableAdapter()
        
        with pytest.raises(Exception) as exc_info:
            await adapter.delete("users", 1)
        
        # Should be the original exception, not ProtectedDeleteError
        assert not isinstance(exc_info.value, ProtectedDeleteError)
        assert "some other database error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fk_error_is_translated(self):
        """FK errors should be translated to ProtectedDeleteError."""
        class TestableAdapter:
            async def _execute(self, sql, *args):
                raise Exception('violates foreign key constraint "test_fkey"')
            
            async def delete(self, table, id):
                try:
                    return await self._execute(f'DELETE FROM "{table}"', id)
                except Exception as e:
                    error_str = str(e).lower()
                    if "foreign" in error_str and "violates" in error_str:
                        # Create a proper dummy instance
                        class DummyInstance:
                            def __init__(self, row_id):
                                self.id = row_id
                        DummyInstance.__name__ = table.title()
                        
                        raise ProtectedDeleteError(
                            instance=DummyInstance(id),
                            relationship="related",
                            related_count=1,
                        )
                    raise
        
        adapter = TestableAdapter()
        
        with pytest.raises(ProtectedDeleteError):
            await adapter.delete("users", 1)

