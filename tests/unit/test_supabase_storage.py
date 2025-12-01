"""
Comprehensive tests for PyNext Supabase Storage.

Tests cover:
- StorageFile and Bucket models
- File upload (bytes, path, file-like)
- File download
- Public and signed URLs
- File listing and deletion
- File move and copy
- Bucket management
- Error handling

Total: 100 tests
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from io import BytesIO

from pynext.db.supabase.storage import (
    SupabaseStorage,
    StorageFile,
    Bucket,
    UploadResult,
    SignedURL,
    _guess_content_type,
    _normalize_path,
)
from pynext.db.supabase.exceptions import (
    StorageError,
    BucketNotFoundError,
    FileNotFoundError,
    UploadError,
    DownloadError,
    PermissionDeniedError,
    FileTooLargeError,
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
    
    storage_client = Mock()
    supabase.client = Mock()
    supabase.client.storage = storage_client
    supabase.admin_client = None
    
    return supabase


@pytest.fixture
def storage(mock_supabase):
    """Create SupabaseStorage instance."""
    return SupabaseStorage(mock_supabase)


@pytest.fixture
def sample_file_data():
    """Sample file data from API."""
    return {
        "name": "avatar.png",
        "id": "file-123",
        "bucket_id": "avatars",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "size": 1024,
        "metadata": {"mimetype": "image/png"},
    }


@pytest.fixture
def sample_bucket_data():
    """Sample bucket data from API."""
    return {
        "id": "avatars",
        "name": "avatars",
        "public": True,
        "created_at": "2024-01-01T00:00:00Z",
        "file_size_limit": 5242880,
        "allowed_mime_types": ["image/*"],
    }


# =============================================================================
# STORAGE FILE MODEL TESTS (15 tests)
# =============================================================================

class TestStorageFileModel:
    """Tests for StorageFile data model."""
    
    def test_storage_file_from_dict_full(self, sample_file_data):
        """StorageFile.from_dict creates file with all fields."""
        file = StorageFile.from_dict(sample_file_data)
        assert file.name == "avatar.png"
        assert file.id == "file-123"
        assert file.bucket_id == "avatars"
    
    def test_storage_file_from_dict_minimal(self):
        """StorageFile.from_dict handles minimal data."""
        file = StorageFile.from_dict({"name": "file.txt"})
        assert file.name == "file.txt"
        assert file.id is None
    
    def test_storage_file_from_dict_size_from_metadata(self):
        """StorageFile.from_dict extracts size from metadata."""
        file = StorageFile.from_dict({
            "name": "file.txt",
            "metadata": {"size": 2048}
        })
        assert file.size == 2048
    
    def test_storage_file_from_dict_mimetype_from_metadata(self):
        """StorageFile.from_dict extracts mimetype from metadata."""
        file = StorageFile.from_dict({
            "name": "file.txt",
            "metadata": {"mimetype": "text/plain"}
        })
        assert file.content_type == "text/plain"
    
    def test_storage_file_datetime_parsing(self, sample_file_data):
        """StorageFile.from_dict parses datetime strings."""
        file = StorageFile.from_dict(sample_file_data)
        assert isinstance(file.created_at, datetime)
    
    def test_storage_file_size_formatted_bytes(self):
        """StorageFile.size_formatted shows bytes."""
        file = StorageFile.from_dict({"name": "f", "size": 500})
        assert "B" in file.size_formatted
    
    def test_storage_file_size_formatted_kb(self):
        """StorageFile.size_formatted shows KB."""
        file = StorageFile.from_dict({"name": "f", "size": 2048})
        assert "KB" in file.size_formatted
    
    def test_storage_file_size_formatted_mb(self):
        """StorageFile.size_formatted shows MB."""
        file = StorageFile.from_dict({"name": "f", "size": 2 * 1024 * 1024})
        assert "MB" in file.size_formatted
    
    def test_storage_file_size_formatted_unknown(self):
        """StorageFile.size_formatted handles None size."""
        file = StorageFile.from_dict({"name": "f"})
        assert file.size_formatted == "unknown"
    
    def test_storage_file_metadata_default(self):
        """StorageFile has empty metadata by default."""
        file = StorageFile.from_dict({"name": "f"})
        assert file.metadata == {}
    
    def test_storage_file_empty_dict(self):
        """StorageFile.from_dict handles empty dict."""
        file = StorageFile.from_dict({})
        assert file.name == ""
    
    def test_storage_file_content_type_direct(self):
        """StorageFile.from_dict uses direct content_type."""
        file = StorageFile.from_dict({
            "name": "f",
            "content_type": "application/pdf"
        })
        assert file.content_type == "application/pdf"
    
    def test_storage_file_created_at_z_suffix(self):
        """StorageFile.from_dict handles Z suffix."""
        file = StorageFile.from_dict({
            "name": "f",
            "created_at": "2024-01-01T00:00:00Z"
        })
        assert file.created_at is not None
    
    def test_storage_file_last_accessed_at(self, sample_file_data):
        """StorageFile.from_dict parses last_accessed_at."""
        sample_file_data["last_accessed_at"] = "2024-01-05T00:00:00Z"
        file = StorageFile.from_dict(sample_file_data)
        assert isinstance(file.last_accessed_at, datetime)
    
    def test_storage_file_all_none_datetimes(self):
        """StorageFile handles None datetime values."""
        file = StorageFile.from_dict({"name": "f"})
        assert file.created_at is None
        assert file.updated_at is None


# =============================================================================
# BUCKET MODEL TESTS (10 tests)
# =============================================================================

class TestBucketModel:
    """Tests for Bucket data model."""
    
    def test_bucket_from_dict_full(self, sample_bucket_data):
        """Bucket.from_dict creates bucket with all fields."""
        bucket = Bucket.from_dict(sample_bucket_data)
        assert bucket.id == "avatars"
        assert bucket.name == "avatars"
        assert bucket.public is True
    
    def test_bucket_from_dict_minimal(self):
        """Bucket.from_dict handles minimal data."""
        bucket = Bucket.from_dict({"id": "docs"})
        assert bucket.id == "docs"
        assert bucket.public is False
    
    def test_bucket_from_dict_file_size_limit(self, sample_bucket_data):
        """Bucket.from_dict parses file_size_limit."""
        bucket = Bucket.from_dict(sample_bucket_data)
        assert bucket.file_size_limit == 5242880
    
    def test_bucket_from_dict_allowed_mime_types(self, sample_bucket_data):
        """Bucket.from_dict parses allowed_mime_types."""
        bucket = Bucket.from_dict(sample_bucket_data)
        assert bucket.allowed_mime_types == ["image/*"]
    
    def test_bucket_from_dict_name_fallback(self):
        """Bucket.from_dict uses id as name fallback."""
        bucket = Bucket.from_dict({"id": "my-bucket"})
        assert bucket.name == "my-bucket"
    
    def test_bucket_datetime_parsing(self, sample_bucket_data):
        """Bucket.from_dict parses datetime strings."""
        bucket = Bucket.from_dict(sample_bucket_data)
        assert isinstance(bucket.created_at, datetime)
    
    def test_bucket_public_default_false(self):
        """Bucket is private by default."""
        bucket = Bucket.from_dict({"id": "private"})
        assert bucket.public is False
    
    def test_bucket_empty_dict(self):
        """Bucket.from_dict handles empty dict."""
        bucket = Bucket.from_dict({})
        assert bucket.id == ""
    
    def test_bucket_updated_at(self, sample_bucket_data):
        """Bucket.from_dict parses updated_at."""
        sample_bucket_data["updated_at"] = "2024-01-03T00:00:00Z"
        bucket = Bucket.from_dict(sample_bucket_data)
        assert isinstance(bucket.updated_at, datetime)
    
    def test_bucket_no_limits(self):
        """Bucket handles None for limits."""
        bucket = Bucket.from_dict({"id": "unlimited"})
        assert bucket.file_size_limit is None
        assert bucket.allowed_mime_types is None


# =============================================================================
# HELPER FUNCTION TESTS (10 tests)
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_guess_content_type_png(self):
        """_guess_content_type returns image/png for .png."""
        assert _guess_content_type("file.png") == "image/png"
    
    def test_guess_content_type_jpg(self):
        """_guess_content_type returns image/jpeg for .jpg."""
        ct = _guess_content_type("file.jpg")
        assert "jpeg" in ct or "jpg" in ct
    
    def test_guess_content_type_pdf(self):
        """_guess_content_type returns application/pdf for .pdf."""
        assert _guess_content_type("file.pdf") == "application/pdf"
    
    def test_guess_content_type_unknown(self):
        """_guess_content_type returns octet-stream for unknown."""
        assert _guess_content_type("file.xyz123") == "application/octet-stream"
    
    def test_guess_content_type_no_extension(self):
        """_guess_content_type handles no extension."""
        assert _guess_content_type("filename") == "application/octet-stream"
    
    def test_normalize_path_removes_leading_slash(self):
        """_normalize_path removes leading slash."""
        assert _normalize_path("/folder/file.txt") == "folder/file.txt"
    
    def test_normalize_path_strips_whitespace(self):
        """_normalize_path strips whitespace."""
        assert _normalize_path("  folder/file.txt  ") == "folder/file.txt"
    
    def test_normalize_path_multiple_slashes(self):
        """_normalize_path removes multiple leading slashes."""
        assert _normalize_path("///folder/file.txt") == "folder/file.txt"
    
    def test_normalize_path_empty(self):
        """_normalize_path handles empty string."""
        assert _normalize_path("") == ""
    
    def test_normalize_path_normal(self):
        """_normalize_path leaves normal path unchanged."""
        assert _normalize_path("folder/file.txt") == "folder/file.txt"


# =============================================================================
# UPLOAD TESTS (20 tests)
# =============================================================================

class TestUpload:
    """Tests for upload method."""
    
    @pytest.mark.asyncio
    async def test_upload_bytes_success(self, storage, mock_supabase):
        """upload accepts bytes."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={"path": "file.png"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        result = await storage.upload("avatars", "file.png", b"file content")
        
        assert isinstance(result, UploadResult)
        assert result.path == "file.png"
    
    @pytest.mark.asyncio
    async def test_upload_returns_full_path(self, storage, mock_supabase):
        """upload returns full path with bucket."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={"path": "folder/file.png"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        result = await storage.upload("avatars", "folder/file.png", b"content")
        
        assert result.full_path == "avatars/folder/file.png"
    
    @pytest.mark.asyncio
    async def test_upload_with_content_type(self, storage, mock_supabase):
        """upload uses provided content type."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.upload("docs", "file.txt", b"content", content_type="text/plain")
        
        call_args = mock_bucket.upload.call_args
        assert call_args[1]["file_options"]["content-type"] == "text/plain"
    
    @pytest.mark.asyncio
    async def test_upload_auto_content_type(self, storage, mock_supabase):
        """upload auto-detects content type from path."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.upload("images", "photo.png", b"content")
        
        call_args = mock_bucket.upload.call_args
        assert call_args[1]["file_options"]["content-type"] == "image/png"
    
    @pytest.mark.asyncio
    async def test_upload_with_upsert(self, storage, mock_supabase):
        """upload passes upsert option."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.upload("bucket", "file.txt", b"content", upsert=True)
        
        call_args = mock_bucket.upload.call_args
        assert call_args[1]["file_options"]["upsert"] == "true"
    
    @pytest.mark.asyncio
    async def test_upload_with_cache_control(self, storage, mock_supabase):
        """upload passes cache_control option."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.upload("bucket", "file.txt", b"content", cache_control="7200")
        
        call_args = mock_bucket.upload.call_args
        assert call_args[1]["file_options"]["cache-control"] == "7200"
    
    @pytest.mark.asyncio
    async def test_upload_normalizes_path(self, storage, mock_supabase):
        """upload normalizes path."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={"path": "folder/file.txt"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.upload("bucket", "/folder/file.txt", b"content")
        
        call_args = mock_bucket.upload.call_args
        assert call_args[1]["path"] == "folder/file.txt"
    
    @pytest.mark.asyncio
    async def test_upload_bucket_not_found(self, storage, mock_supabase):
        """upload raises BucketNotFoundError."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(side_effect=Exception("Bucket not found"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(BucketNotFoundError):
            await storage.upload("nonexistent", "file.txt", b"content")
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, storage, mock_supabase):
        """upload raises FileTooLargeError."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(side_effect=Exception("File too large"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(FileTooLargeError):
            await storage.upload("bucket", "file.txt", b"x" * 1000000)
    
    @pytest.mark.asyncio
    async def test_upload_permission_denied(self, storage, mock_supabase):
        """upload raises PermissionDeniedError."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(side_effect=Exception("Permission denied"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(PermissionDeniedError):
            await storage.upload("bucket", "file.txt", b"content")
    
    @pytest.mark.asyncio
    async def test_upload_generic_error(self, storage, mock_supabase):
        """upload raises UploadError for generic errors."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(side_effect=Exception("Network error"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(UploadError):
            await storage.upload("bucket", "file.txt", b"content")
    
    @pytest.mark.asyncio
    async def test_upload_from_path_string(self, storage, mock_supabase, tmp_path):
        """upload accepts file path string."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={"path": "file.txt"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        # Create temp file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        result = await storage.upload("bucket", "file.txt", str(test_file))
        
        assert result.path == "file.txt"
    
    @pytest.mark.asyncio
    async def test_upload_from_path_object(self, storage, mock_supabase, tmp_path):
        """upload accepts Path object."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={"path": "file.txt"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        
        result = await storage.upload("bucket", "file.txt", test_file)
        
        assert result.path == "file.txt"
    
    @pytest.mark.asyncio
    async def test_upload_from_file_object(self, storage, mock_supabase):
        """upload accepts file-like object."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={"path": "file.txt"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        file_obj = BytesIO(b"file content")
        
        result = await storage.upload("bucket", "file.txt", file_obj)
        
        assert result.path == "file.txt"
    
    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, storage, mock_supabase):
        """upload raises UploadError for missing file."""
        mock_bucket = Mock()
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(UploadError):
            await storage.upload("bucket", "file.txt", "/nonexistent/path.txt")
    
    @pytest.mark.asyncio
    async def test_upload_content_type_from_file_path(self, storage, mock_supabase, tmp_path):
        """upload detects content type from local file."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        test_file = tmp_path / "image.png"
        test_file.write_bytes(b"png content")
        
        await storage.upload("bucket", "dest.txt", test_file)
        
        call_args = mock_bucket.upload.call_args
        assert call_args[1]["file_options"]["content-type"] == "image/png"
    
    @pytest.mark.asyncio
    async def test_upload_policy_error(self, storage, mock_supabase):
        """upload handles policy violation error."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(side_effect=Exception("Policy violation"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(PermissionDeniedError):
            await storage.upload("bucket", "file.txt", b"content")
    
    @pytest.mark.asyncio
    async def test_upload_size_error_variant(self, storage, mock_supabase):
        """upload handles 'size' in error message."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(side_effect=Exception("Payload size exceeded"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(FileTooLargeError):
            await storage.upload("bucket", "file.txt", b"content")
    
    @pytest.mark.asyncio
    async def test_upload_returns_id_when_present(self, storage, mock_supabase):
        """upload returns ID from response."""
        mock_bucket = Mock()
        mock_bucket.upload = Mock(return_value={"path": "file.txt", "Id": "uuid-123"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        result = await storage.upload("bucket", "file.txt", b"content")
        
        assert result.id == "uuid-123"


# =============================================================================
# DOWNLOAD TESTS (10 tests)
# =============================================================================

class TestDownload:
    """Tests for download method."""
    
    @pytest.mark.asyncio
    async def test_download_success(self, storage, mock_supabase):
        """download returns file bytes."""
        mock_bucket = Mock()
        mock_bucket.download = Mock(return_value=b"file content")
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        data = await storage.download("bucket", "file.txt")
        
        assert data == b"file content"
    
    @pytest.mark.asyncio
    async def test_download_normalizes_path(self, storage, mock_supabase):
        """download normalizes path."""
        mock_bucket = Mock()
        mock_bucket.download = Mock(return_value=b"content")
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.download("bucket", "/folder/file.txt")
        
        mock_bucket.download.assert_called_with("folder/file.txt")
    
    @pytest.mark.asyncio
    async def test_download_file_not_found(self, storage, mock_supabase):
        """download raises FileNotFoundError."""
        mock_bucket = Mock()
        mock_bucket.download = Mock(side_effect=Exception("Object not found"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(FileNotFoundError):
            await storage.download("bucket", "nonexistent.txt")
    
    @pytest.mark.asyncio
    async def test_download_bucket_not_found(self, storage, mock_supabase):
        """download raises BucketNotFoundError."""
        mock_bucket = Mock()
        mock_bucket.download = Mock(side_effect=Exception("Bucket not found"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(BucketNotFoundError):
            await storage.download("nonexistent", "file.txt")
    
    @pytest.mark.asyncio
    async def test_download_permission_denied(self, storage, mock_supabase):
        """download raises PermissionDeniedError."""
        mock_bucket = Mock()
        mock_bucket.download = Mock(side_effect=Exception("Permission denied"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(PermissionDeniedError):
            await storage.download("bucket", "private.txt")
    
    @pytest.mark.asyncio
    async def test_download_generic_error(self, storage, mock_supabase):
        """download raises DownloadError for generic errors."""
        mock_bucket = Mock()
        mock_bucket.download = Mock(side_effect=Exception("Network error"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(DownloadError):
            await storage.download("bucket", "file.txt")
    
    @pytest.mark.asyncio
    async def test_download_file_not_found_variant(self, storage, mock_supabase):
        """download handles 'file not found' variant."""
        mock_bucket = Mock()
        mock_bucket.download = Mock(side_effect=Exception("File not found"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(FileNotFoundError) as exc_info:
            await storage.download("bucket", "missing.txt")
        
        assert "missing.txt" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_download_calls_correct_bucket(self, storage, mock_supabase):
        """download uses correct bucket."""
        mock_bucket = Mock()
        mock_bucket.download = Mock(return_value=b"content")
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.download("my-bucket", "file.txt")
        
        mock_supabase.client.storage.from_.assert_called_with("my-bucket")
    
    @pytest.mark.asyncio
    async def test_download_binary_content(self, storage, mock_supabase):
        """download returns binary content."""
        binary_data = bytes(range(256))
        mock_bucket = Mock()
        mock_bucket.download = Mock(return_value=binary_data)
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        data = await storage.download("bucket", "file.bin")
        
        assert data == binary_data
    
    @pytest.mark.asyncio
    async def test_download_large_file(self, storage, mock_supabase):
        """download handles large files."""
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        mock_bucket = Mock()
        mock_bucket.download = Mock(return_value=large_content)
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        data = await storage.download("bucket", "large.bin")
        
        assert len(data) == 10 * 1024 * 1024


# =============================================================================
# URL TESTS (15 tests)
# =============================================================================

class TestURLs:
    """Tests for URL generation methods."""
    
    def test_get_public_url_success(self, storage, mock_supabase):
        """get_public_url returns URL."""
        mock_bucket = Mock()
        mock_bucket.get_public_url = Mock(return_value="https://example.com/file.png")
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        url = storage.get_public_url("bucket", "file.png")
        
        assert url == "https://example.com/file.png"
    
    def test_get_public_url_normalizes_path(self, storage, mock_supabase):
        """get_public_url normalizes path."""
        mock_bucket = Mock()
        mock_bucket.get_public_url = Mock(return_value="url")
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        storage.get_public_url("bucket", "/folder/file.png")
        
        mock_bucket.get_public_url.assert_called_with("folder/file.png")
    
    def test_get_public_url_dict_response(self, storage, mock_supabase):
        """get_public_url handles dict response."""
        mock_bucket = Mock()
        mock_bucket.get_public_url = Mock(return_value={"publicUrl": "https://example.com/f"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        url = storage.get_public_url("bucket", "file.png")
        
        assert url == "https://example.com/f"
    
    def test_get_public_url_publicURL_variant(self, storage, mock_supabase):
        """get_public_url handles publicURL key."""
        mock_bucket = Mock()
        mock_bucket.get_public_url = Mock(return_value={"publicURL": "https://example.com/f"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        url = storage.get_public_url("bucket", "file.png")
        
        assert url == "https://example.com/f"
    
    @pytest.mark.asyncio
    async def test_get_signed_url_success(self, storage, mock_supabase):
        """get_signed_url returns signed URL."""
        mock_bucket = Mock()
        mock_bucket.create_signed_url = Mock(return_value={"signedUrl": "https://example.com/signed"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        url = await storage.get_signed_url("bucket", "file.png")
        
        assert url == "https://example.com/signed"
    
    @pytest.mark.asyncio
    async def test_get_signed_url_default_expiry(self, storage, mock_supabase):
        """get_signed_url uses default 1 hour expiry."""
        mock_bucket = Mock()
        mock_bucket.create_signed_url = Mock(return_value={"signedUrl": "url"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.get_signed_url("bucket", "file.png")
        
        call_args = mock_bucket.create_signed_url.call_args
        assert call_args[1]["expires_in"] == 3600
    
    @pytest.mark.asyncio
    async def test_get_signed_url_custom_expiry(self, storage, mock_supabase):
        """get_signed_url accepts custom expiry."""
        mock_bucket = Mock()
        mock_bucket.create_signed_url = Mock(return_value={"signedUrl": "url"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.get_signed_url("bucket", "file.png", expires_in=7200)
        
        call_args = mock_bucket.create_signed_url.call_args
        assert call_args[1]["expires_in"] == 7200
    
    @pytest.mark.asyncio
    async def test_get_signed_url_with_download(self, storage, mock_supabase):
        """get_signed_url passes download option."""
        mock_bucket = Mock()
        mock_bucket.create_signed_url = Mock(return_value={"signedUrl": "url"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.get_signed_url("bucket", "file.pdf", download="report.pdf")
        
        call_args = mock_bucket.create_signed_url.call_args
        assert call_args[1]["options"]["download"] == "report.pdf"
    
    @pytest.mark.asyncio
    async def test_get_signed_url_with_transform(self, storage, mock_supabase):
        """get_signed_url passes transform option."""
        mock_bucket = Mock()
        mock_bucket.create_signed_url = Mock(return_value={"signedUrl": "url"})
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.get_signed_url(
            "bucket", "image.png",
            transform={"width": 200, "height": 200}
        )
        
        call_args = mock_bucket.create_signed_url.call_args
        assert call_args[1]["options"]["transform"]["width"] == 200
    
    @pytest.mark.asyncio
    async def test_get_signed_url_file_not_found(self, storage, mock_supabase):
        """get_signed_url raises FileNotFoundError."""
        mock_bucket = Mock()
        mock_bucket.create_signed_url = Mock(side_effect=Exception("Not found"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(FileNotFoundError):
            await storage.get_signed_url("bucket", "missing.txt")
    
    @pytest.mark.asyncio
    async def test_get_signed_url_generic_error(self, storage, mock_supabase):
        """get_signed_url raises StorageError for generic errors."""
        mock_bucket = Mock()
        mock_bucket.create_signed_url = Mock(side_effect=Exception("Network error"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(StorageError):
            await storage.get_signed_url("bucket", "file.txt")
    
    @pytest.mark.asyncio
    async def test_get_signed_urls_multiple(self, storage, mock_supabase):
        """get_signed_urls returns multiple URLs."""
        mock_bucket = Mock()
        mock_bucket.create_signed_urls = Mock(return_value=[
            {"signedUrl": "url1", "path": "file1.txt"},
            {"signedUrl": "url2", "path": "file2.txt"},
        ])
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        urls = await storage.get_signed_urls("bucket", ["file1.txt", "file2.txt"])
        
        assert len(urls) == 2
        assert all(isinstance(u, SignedURL) for u in urls)
    
    @pytest.mark.asyncio
    async def test_get_signed_urls_normalizes_paths(self, storage, mock_supabase):
        """get_signed_urls normalizes paths."""
        mock_bucket = Mock()
        mock_bucket.create_signed_urls = Mock(return_value=[])
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.get_signed_urls("bucket", ["/file1.txt", "/file2.txt"])
        
        call_args = mock_bucket.create_signed_urls.call_args
        assert call_args[1]["paths"] == ["file1.txt", "file2.txt"]
    
    @pytest.mark.asyncio
    async def test_get_signed_urls_error(self, storage, mock_supabase):
        """get_signed_urls raises StorageError."""
        mock_bucket = Mock()
        mock_bucket.create_signed_urls = Mock(side_effect=Exception("Error"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(StorageError):
            await storage.get_signed_urls("bucket", ["file.txt"])


# =============================================================================
# FILE MANAGEMENT TESTS (10 tests)
# =============================================================================

class TestFileManagement:
    """Tests for file management methods."""
    
    @pytest.mark.asyncio
    async def test_delete_single_file(self, storage, mock_supabase):
        """delete removes single file."""
        mock_bucket = Mock()
        mock_bucket.remove = Mock(return_value=[{"name": "file.txt"}])
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        deleted = await storage.delete("bucket", "file.txt")
        
        assert "file.txt" in deleted
    
    @pytest.mark.asyncio
    async def test_delete_multiple_files(self, storage, mock_supabase):
        """delete removes multiple files."""
        mock_bucket = Mock()
        mock_bucket.remove = Mock(return_value=[{"name": "f1.txt"}, {"name": "f2.txt"}])
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        deleted = await storage.delete("bucket", ["f1.txt", "f2.txt"])
        
        assert len(deleted) == 2
    
    @pytest.mark.asyncio
    async def test_delete_bucket_not_found(self, storage, mock_supabase):
        """delete raises BucketNotFoundError."""
        mock_bucket = Mock()
        mock_bucket.remove = Mock(side_effect=Exception("Bucket not found"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(BucketNotFoundError):
            await storage.delete("nonexistent", "file.txt")
    
    @pytest.mark.asyncio
    async def test_list_files(self, storage, mock_supabase, sample_file_data):
        """list returns file list."""
        mock_bucket = Mock()
        mock_bucket.list = Mock(return_value=[sample_file_data])
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        files = await storage.list("bucket")
        
        assert len(files) == 1
        assert isinstance(files[0], StorageFile)
    
    @pytest.mark.asyncio
    async def test_list_with_path(self, storage, mock_supabase):
        """list accepts path parameter."""
        mock_bucket = Mock()
        mock_bucket.list = Mock(return_value=[])
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.list("bucket", "folder/")
        
        call_args = mock_bucket.list.call_args
        assert call_args[1]["path"] == "folder/"
    
    @pytest.mark.asyncio
    async def test_list_with_limit(self, storage, mock_supabase):
        """list accepts limit parameter."""
        mock_bucket = Mock()
        mock_bucket.list = Mock(return_value=[])
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.list("bucket", limit=50)
        
        call_args = mock_bucket.list.call_args
        assert call_args[1]["options"]["limit"] == 50
    
    @pytest.mark.asyncio
    async def test_move_file(self, storage, mock_supabase):
        """move renames file."""
        mock_bucket = Mock()
        mock_bucket.move = Mock()
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.move("bucket", "old.txt", "new.txt")
        
        mock_bucket.move.assert_called_with("old.txt", "new.txt")
    
    @pytest.mark.asyncio
    async def test_copy_file(self, storage, mock_supabase):
        """copy duplicates file."""
        mock_bucket = Mock()
        mock_bucket.copy = Mock()
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        await storage.copy("bucket", "source.txt", "dest.txt")
        
        mock_bucket.copy.assert_called_with("source.txt", "dest.txt")
    
    @pytest.mark.asyncio
    async def test_move_error(self, storage, mock_supabase):
        """move raises StorageError."""
        mock_bucket = Mock()
        mock_bucket.move = Mock(side_effect=Exception("Error"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(StorageError):
            await storage.move("bucket", "old.txt", "new.txt")
    
    @pytest.mark.asyncio
    async def test_copy_error(self, storage, mock_supabase):
        """copy raises StorageError."""
        mock_bucket = Mock()
        mock_bucket.copy = Mock(side_effect=Exception("Error"))
        mock_supabase.client.storage.from_ = Mock(return_value=mock_bucket)
        
        with pytest.raises(StorageError):
            await storage.copy("bucket", "source.txt", "dest.txt")


# =============================================================================
# BUCKET MANAGEMENT TESTS (10 tests)
# =============================================================================

class TestBucketManagement:
    """Tests for bucket management methods."""
    
    @pytest.mark.asyncio
    async def test_create_bucket(self, storage, mock_supabase):
        """create_bucket creates new bucket."""
        mock_supabase.client.storage.create_bucket = Mock(return_value={})
        
        bucket = await storage.create_bucket("new-bucket")
        
        assert isinstance(bucket, Bucket)
        assert bucket.id == "new-bucket"
    
    @pytest.mark.asyncio
    async def test_create_bucket_public(self, storage, mock_supabase):
        """create_bucket with public=True."""
        mock_supabase.client.storage.create_bucket = Mock(return_value={})
        
        bucket = await storage.create_bucket("public-bucket", public=True)
        
        call_args = mock_supabase.client.storage.create_bucket.call_args
        assert call_args[1]["options"]["public"] is True
    
    @pytest.mark.asyncio
    async def test_create_bucket_with_limits(self, storage, mock_supabase):
        """create_bucket with file size limit."""
        mock_supabase.client.storage.create_bucket = Mock(return_value={})
        
        await storage.create_bucket("limited", file_size_limit=1024)
        
        call_args = mock_supabase.client.storage.create_bucket.call_args
        assert call_args[1]["options"]["file_size_limit"] == 1024
    
    @pytest.mark.asyncio
    async def test_get_bucket(self, storage, mock_supabase, sample_bucket_data):
        """get_bucket returns bucket info."""
        mock_supabase.client.storage.get_bucket = Mock(return_value=sample_bucket_data)
        
        bucket = await storage.get_bucket("avatars")
        
        assert isinstance(bucket, Bucket)
        assert bucket.id == "avatars"
    
    @pytest.mark.asyncio
    async def test_get_bucket_not_found(self, storage, mock_supabase):
        """get_bucket raises BucketNotFoundError."""
        mock_supabase.client.storage.get_bucket = Mock(side_effect=Exception("Not found"))
        
        with pytest.raises(BucketNotFoundError):
            await storage.get_bucket("nonexistent")
    
    @pytest.mark.asyncio
    async def test_list_buckets(self, storage, mock_supabase, sample_bucket_data):
        """list_buckets returns all buckets."""
        mock_supabase.client.storage.list_buckets = Mock(return_value=[sample_bucket_data])
        
        buckets = await storage.list_buckets()
        
        assert len(buckets) == 1
        assert isinstance(buckets[0], Bucket)
    
    @pytest.mark.asyncio
    async def test_update_bucket(self, storage, mock_supabase, sample_bucket_data):
        """update_bucket modifies bucket settings."""
        mock_supabase.client.storage.update_bucket = Mock(return_value=sample_bucket_data)
        
        bucket = await storage.update_bucket("avatars", public=False)
        
        assert isinstance(bucket, Bucket)
    
    @pytest.mark.asyncio
    async def test_delete_bucket(self, storage, mock_supabase):
        """delete_bucket removes bucket."""
        mock_supabase.client.storage.delete_bucket = Mock()
        
        await storage.delete_bucket("empty-bucket")
        
        mock_supabase.client.storage.delete_bucket.assert_called_with("empty-bucket")
    
    @pytest.mark.asyncio
    async def test_empty_bucket(self, storage, mock_supabase):
        """empty_bucket removes all files."""
        mock_supabase.client.storage.empty_bucket = Mock()
        
        await storage.empty_bucket("bucket-to-empty")
        
        mock_supabase.client.storage.empty_bucket.assert_called_with("bucket-to-empty")
    
    @pytest.mark.asyncio
    async def test_delete_bucket_not_found(self, storage, mock_supabase):
        """delete_bucket raises BucketNotFoundError."""
        mock_supabase.client.storage.delete_bucket = Mock(side_effect=Exception("Not found"))
        
        with pytest.raises(BucketNotFoundError):
            await storage.delete_bucket("nonexistent")

