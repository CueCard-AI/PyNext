"""
PyNext Supabase Storage.

Provides a simple API for Supabase Storage operations:
- File upload and download
- Public and signed URLs
- Bucket management
- File listing and deletion

Why This Exists:
    Supabase Storage API is straightforward, but we add:
    - Automatic content-type detection
    - Support for file paths, bytes, and file-like objects
    - Better error handling with specific exceptions
    - Async-first design

Usage (Stupid Easy):
    from pynext.db.supabase import Supabase
    
    db = Supabase("https://xyz.supabase.co")
    
    # Upload file
    await db.storage.upload("avatars", "user_123.png", file_data)
    
    # Download file
    data = await db.storage.download("avatars", "user_123.png")
    
    # Get public URL
    url = db.storage.get_public_url("avatars", "user_123.png")
    
    # Delete file
    await db.storage.delete("avatars", "user_123.png")
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union, TYPE_CHECKING
import mimetypes
import os

from .exceptions import (
    StorageError,
    BucketNotFoundError,
    FileNotFoundError,
    UploadError,
    DownloadError,
    PermissionDeniedError,
    FileTooLargeError,
    from_supabase_exception,
)

if TYPE_CHECKING:
    from .adapter import Supabase


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class StorageFile:
    """
    File metadata from Supabase Storage.
    
    Attributes:
        name: File name
        id: Unique file ID
        bucket_id: Bucket the file is in
        created_at: When the file was created
        updated_at: When the file was last updated
        last_accessed_at: When the file was last accessed
        size: File size in bytes
        content_type: MIME type of the file
        metadata: Additional file metadata
    """
    name: str
    id: Optional[str] = None
    bucket_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    size: Optional[int] = None
    content_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StorageFile":
        """Create StorageFile from dictionary."""
        return cls(
            name=data.get("name", ""),
            id=data.get("id"),
            bucket_id=data.get("bucket_id"),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
            last_accessed_at=_parse_datetime(data.get("last_accessed_at")),
            size=data.get("size") or data.get("metadata", {}).get("size"),
            content_type=data.get("content_type") or data.get("metadata", {}).get("mimetype"),
            metadata=data.get("metadata", {}),
        )
    
    @property
    def size_formatted(self) -> str:
        """Get human-readable file size."""
        if self.size is None:
            return "unknown"
        
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if abs(self.size) < 1024.0:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.1f} PB"


@dataclass
class Bucket:
    """
    Storage bucket configuration.
    
    Attributes:
        id: Unique bucket ID (same as name)
        name: Bucket name
        public: Whether bucket is publicly accessible
        created_at: When the bucket was created
        updated_at: When the bucket was last updated
        file_size_limit: Maximum file size in bytes (None = no limit)
        allowed_mime_types: Allowed MIME types (None = all allowed)
    """
    id: str
    name: str
    public: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    file_size_limit: Optional[int] = None
    allowed_mime_types: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Bucket":
        """Create Bucket from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", data.get("id", "")),
            public=data.get("public", False),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
            file_size_limit=data.get("file_size_limit"),
            allowed_mime_types=data.get("allowed_mime_types"),
        )


@dataclass
class UploadResult:
    """
    Result of a file upload.
    
    Attributes:
        path: Full path to the uploaded file
        id: Unique file ID
        full_path: Full path including bucket
    """
    path: str
    id: Optional[str] = None
    full_path: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UploadResult":
        """Create UploadResult from dictionary."""
        return cls(
            path=data.get("path", data.get("Key", "")),
            id=data.get("Id", data.get("id")),
            full_path=data.get("fullPath", data.get("Key")),
        )


@dataclass
class SignedURL:
    """
    Signed URL for temporary file access.
    
    Attributes:
        signed_url: The signed URL
        path: Path to the file
        token: Token portion of URL
        error: Any error that occurred
    """
    signed_url: str
    path: Optional[str] = None
    token: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string to datetime object."""
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def _guess_content_type(filename: str) -> str:
    """Guess content type from filename."""
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


def _normalize_path(path: str) -> str:
    """Normalize file path (remove leading slashes, etc.)."""
    return path.lstrip("/").strip()


# =============================================================================
# MAIN STORAGE CLASS
# =============================================================================

class SupabaseStorage:
    """
    Supabase Storage service.
    
    Handles file operations:
    - Upload files (bytes, file path, or file-like object)
    - Download files
    - Get public and signed URLs
    - List and delete files
    - Manage buckets
    
    Usage:
        db = Supabase("https://xyz.supabase.co")
        
        # Upload file
        await db.storage.upload("avatars", "user_123.png", file_bytes)
        
        # Download
        data = await db.storage.download("avatars", "user_123.png")
        
        # Get URL
        url = db.storage.get_public_url("avatars", "user_123.png")
    """
    
    def __init__(self, supabase: "Supabase"):
        """
        Initialize storage service.
        
        Args:
            supabase: Parent Supabase adapter instance
        """
        self._supabase = supabase
    
    @property
    def _client(self):
        """Get the underlying supabase-py storage client."""
        self._supabase._ensure_initialized()
        return self._supabase.client.storage
    
    def _get_bucket(self, bucket_name: str):
        """Get a bucket reference."""
        return self._client.from_(bucket_name)
    
    # =========================================================================
    # FILE UPLOAD
    # =========================================================================
    
    async def upload(
        self,
        bucket: str,
        path: str,
        file: Union[bytes, str, Path, BinaryIO],
        *,
        content_type: Optional[str] = None,
        upsert: bool = False,
        cache_control: str = "3600",
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """
        Upload a file to storage.
        
        Args:
            bucket: Bucket name
            path: Path within bucket (e.g., "folder/file.png")
            file: File data - can be:
                - bytes: Raw file bytes
                - str or Path: Path to a local file
                - BinaryIO: File-like object (opened in binary mode)
            content_type: MIME type (auto-detected if not provided)
            upsert: If True, overwrite existing file (default: False)
            cache_control: Cache-Control header value
            metadata: Additional metadata to store with file
        
        Returns:
            UploadResult with path and ID
        
        Raises:
            BucketNotFoundError: If bucket doesn't exist
            UploadError: If upload fails
            FileTooLargeError: If file exceeds size limit
        
        Example:
            # Upload bytes
            await db.storage.upload("avatars", "user_123.png", image_bytes)
            
            # Upload from file path
            await db.storage.upload("documents", "report.pdf", "/path/to/report.pdf")
            
            # Upload with metadata
            await db.storage.upload(
                "assets",
                "image.jpg",
                image_bytes,
                metadata={"author": "Alice", "version": "1.0"}
            )
        """
        path = _normalize_path(path)
        
        # Resolve file data
        file_data: bytes
        if isinstance(file, bytes):
            file_data = file
        elif isinstance(file, (str, Path)):
            file_path = Path(file)
            if not file_path.exists():
                raise UploadError(bucket=bucket, path=path, reason=f"File not found: {file}")
            file_data = file_path.read_bytes()
            if not content_type:
                content_type = _guess_content_type(str(file_path))
        else:
            # File-like object
            file_data = file.read()
        
        # Auto-detect content type from path
        if not content_type:
            content_type = _guess_content_type(path)
        
        try:
            # Build options
            file_options = {
                "content-type": content_type,
                "cache-control": cache_control,
                "upsert": str(upsert).lower(),
            }
            if metadata:
                file_options["x-upsert"] = str(upsert).lower()
            
            response = self._get_bucket(bucket).upload(
                path=path,
                file=file_data,
                file_options=file_options,
            )
            
            return UploadResult(
                path=path,
                id=response.get("Id") if isinstance(response, dict) else None,
                full_path=f"{bucket}/{path}",
            )
            
        except Exception as e:
            error_str = str(e).lower()
            if "bucket" in error_str and "not found" in error_str:
                raise BucketNotFoundError(bucket=bucket)
            if "too large" in error_str or "size" in error_str:
                raise FileTooLargeError(size_bytes=len(file_data), max_bytes=0)
            if "permission" in error_str or "denied" in error_str or "policy" in error_str:
                raise PermissionDeniedError(bucket=bucket, operation="upload")
            raise UploadError(bucket=bucket, path=path, reason=str(e))
    
    async def upload_to_signed_url(
        self,
        bucket: str,
        path: str,
        token: str,
        file: Union[bytes, str, Path, BinaryIO],
        *,
        content_type: Optional[str] = None,
    ) -> UploadResult:
        """
        Upload a file using a pre-signed URL.
        
        This is useful for uploading from the client side without
        exposing credentials.
        
        Args:
            bucket: Bucket name
            path: Path within bucket
            token: Token from create_signed_upload_url
            file: File data
            content_type: MIME type
        
        Returns:
            UploadResult
        """
        path = _normalize_path(path)
        
        # Resolve file data
        file_data: bytes
        if isinstance(file, bytes):
            file_data = file
        elif isinstance(file, (str, Path)):
            file_data = Path(file).read_bytes()
        else:
            file_data = file.read()
        
        if not content_type:
            content_type = _guess_content_type(path)
        
        try:
            response = self._get_bucket(bucket).upload_to_signed_url(
                path=path,
                token=token,
                file=file_data,
                file_options={"content-type": content_type},
            )
            
            return UploadResult(path=path, full_path=f"{bucket}/{path}")
            
        except Exception as e:
            raise UploadError(bucket=bucket, path=path, reason=str(e))
    
    async def create_signed_upload_url(
        self,
        bucket: str,
        path: str,
    ) -> SignedURL:
        """
        Create a signed URL for uploading.
        
        This allows clients to upload directly without your API key.
        
        Args:
            bucket: Bucket name
            path: Path where file will be uploaded
        
        Returns:
            SignedURL with token for upload
        
        Example:
            # On server
            signed = await db.storage.create_signed_upload_url("uploads", "file.pdf")
            
            # Send signed_url to client
            # Client uploads directly to signed_url
        """
        path = _normalize_path(path)
        
        try:
            response = self._get_bucket(bucket).create_signed_upload_url(path)
            return SignedURL(
                signed_url=response.get("signedUrl", response.get("signed_url", "")),
                path=path,
                token=response.get("token"),
            )
        except Exception as e:
            raise StorageError(message=f"Failed to create signed upload URL: {e}")
    
    # =========================================================================
    # FILE DOWNLOAD
    # =========================================================================
    
    async def download(
        self,
        bucket: str,
        path: str,
    ) -> bytes:
        """
        Download a file from storage.
        
        Args:
            bucket: Bucket name
            path: Path to the file
        
        Returns:
            File contents as bytes
        
        Raises:
            FileNotFoundError: If file doesn't exist
            BucketNotFoundError: If bucket doesn't exist
            DownloadError: If download fails
        
        Example:
            data = await db.storage.download("avatars", "user_123.png")
            
            # Save to local file
            with open("avatar.png", "wb") as f:
                f.write(data)
        """
        path = _normalize_path(path)
        
        try:
            response = self._get_bucket(bucket).download(path)
            return response
            
        except Exception as e:
            error_str = str(e).lower()
            if "not found" in error_str:
                if "bucket" in error_str:
                    raise BucketNotFoundError(bucket=bucket)
                raise FileNotFoundError(bucket=bucket, path=path)
            if "permission" in error_str or "denied" in error_str:
                raise PermissionDeniedError(bucket=bucket, operation="download")
            raise DownloadError(bucket=bucket, path=path, reason=str(e))
    
    # =========================================================================
    # FILE URLS
    # =========================================================================
    
    def get_public_url(self, bucket: str, path: str) -> str:
        """
        Get the public URL for a file.
        
        Note: Only works for public buckets.
        
        Args:
            bucket: Bucket name
            path: Path to the file
        
        Returns:
            Public URL string
        
        Example:
            url = db.storage.get_public_url("avatars", "user_123.png")
            # Returns: https://xyz.supabase.co/storage/v1/object/public/avatars/user_123.png
        """
        path = _normalize_path(path)
        response = self._get_bucket(bucket).get_public_url(path)
        
        # Handle different response formats
        if isinstance(response, dict):
            return response.get("publicUrl", response.get("publicURL", ""))
        return str(response)
    
    async def get_signed_url(
        self,
        bucket: str,
        path: str,
        expires_in: int = 3600,
        *,
        download: Optional[str] = None,
        transform: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get a signed URL for private file access.
        
        The URL will be valid for the specified duration.
        
        Args:
            bucket: Bucket name
            path: Path to the file
            expires_in: Seconds until URL expires (default: 1 hour)
            download: If provided, sets Content-Disposition to attachment
                      with this filename
            transform: Image transformations (width, height, resize, etc.)
        
        Returns:
            Signed URL string
        
        Example:
            # URL valid for 1 hour
            url = await db.storage.get_signed_url("private", "secret.pdf")
            
            # URL valid for 1 day, downloads as "report.pdf"
            url = await db.storage.get_signed_url(
                "documents",
                "reports/2024-01.pdf",
                expires_in=86400,
                download="report.pdf"
            )
        """
        path = _normalize_path(path)
        
        try:
            options = {}
            if download:
                options["download"] = download
            if transform:
                options["transform"] = transform
            
            response = self._get_bucket(bucket).create_signed_url(
                path=path,
                expires_in=expires_in,
                options=options if options else None,
            )
            
            if isinstance(response, dict):
                return response.get("signedUrl", response.get("signedURL", ""))
            return str(response)
            
        except Exception as e:
            error_str = str(e).lower()
            if "not found" in error_str:
                raise FileNotFoundError(bucket=bucket, path=path)
            raise StorageError(message=f"Failed to create signed URL: {e}")
    
    async def get_signed_urls(
        self,
        bucket: str,
        paths: List[str],
        expires_in: int = 3600,
    ) -> List[SignedURL]:
        """
        Get signed URLs for multiple files.
        
        More efficient than calling get_signed_url multiple times.
        
        Args:
            bucket: Bucket name
            paths: List of file paths
            expires_in: Seconds until URLs expire
        
        Returns:
            List of SignedURL objects
        """
        paths = [_normalize_path(p) for p in paths]
        
        try:
            response = self._get_bucket(bucket).create_signed_urls(
                paths=paths,
                expires_in=expires_in,
            )
            
            return [
                SignedURL(
                    signed_url=r.get("signedUrl", r.get("signedURL", "")),
                    path=r.get("path"),
                    error=r.get("error"),
                )
                for r in response
            ]
            
        except Exception as e:
            raise StorageError(message=f"Failed to create signed URLs: {e}")
    
    # =========================================================================
    # FILE MANAGEMENT
    # =========================================================================
    
    async def delete(
        self,
        bucket: str,
        paths: Union[str, List[str]],
    ) -> List[str]:
        """
        Delete one or more files.
        
        Args:
            bucket: Bucket name
            paths: Path or list of paths to delete
        
        Returns:
            List of deleted paths
        
        Example:
            # Delete single file
            await db.storage.delete("avatars", "old_avatar.png")
            
            # Delete multiple files
            await db.storage.delete("temp", ["file1.txt", "file2.txt", "file3.txt"])
        """
        if isinstance(paths, str):
            paths = [paths]
        paths = [_normalize_path(p) for p in paths]
        
        try:
            response = self._get_bucket(bucket).remove(paths)
            
            # Extract deleted paths from response
            if isinstance(response, list):
                return [r.get("name", r.get("Key", "")) for r in response]
            return paths
            
        except Exception as e:
            error_str = str(e).lower()
            if "bucket" in error_str and "not found" in error_str:
                raise BucketNotFoundError(bucket=bucket)
            if "permission" in error_str or "denied" in error_str:
                raise PermissionDeniedError(bucket=bucket, operation="delete")
            raise StorageError(message=f"Failed to delete files: {e}")
    
    async def list(
        self,
        bucket: str,
        path: str = "",
        *,
        limit: int = 100,
        offset: int = 0,
        sort_by: Optional[Dict[str, str]] = None,
        search: Optional[str] = None,
    ) -> List[StorageFile]:
        """
        List files in a bucket/folder.
        
        Args:
            bucket: Bucket name
            path: Folder path (empty for root)
            limit: Maximum files to return
            offset: Pagination offset
            sort_by: Sort options (column, order)
            search: Search query
        
        Returns:
            List of StorageFile objects
        
        Example:
            # List all files in bucket
            files = await db.storage.list("avatars")
            
            # List files in folder
            files = await db.storage.list("documents", "reports/2024/")
            
            # Search files
            files = await db.storage.list("assets", search="logo")
        """
        path = _normalize_path(path) if path else ""
        
        try:
            options = {
                "limit": limit,
                "offset": offset,
            }
            if sort_by:
                options["sortBy"] = sort_by
            if search:
                options["search"] = search
            
            response = self._get_bucket(bucket).list(path=path, options=options)
            
            return [StorageFile.from_dict(f) for f in response]
            
        except Exception as e:
            error_str = str(e).lower()
            if "bucket" in error_str and "not found" in error_str:
                raise BucketNotFoundError(bucket=bucket)
            raise StorageError(message=f"Failed to list files: {e}")
    
    async def move(
        self,
        bucket: str,
        from_path: str,
        to_path: str,
    ) -> None:
        """
        Move/rename a file within a bucket.
        
        Args:
            bucket: Bucket name
            from_path: Current file path
            to_path: New file path
        
        Example:
            await db.storage.move("docs", "old_name.pdf", "new_name.pdf")
        """
        from_path = _normalize_path(from_path)
        to_path = _normalize_path(to_path)
        
        try:
            self._get_bucket(bucket).move(from_path, to_path)
        except Exception as e:
            raise StorageError(message=f"Failed to move file: {e}")
    
    async def copy(
        self,
        bucket: str,
        from_path: str,
        to_path: str,
    ) -> None:
        """
        Copy a file within a bucket.
        
        Args:
            bucket: Bucket name
            from_path: Source file path
            to_path: Destination file path
        
        Example:
            await db.storage.copy("docs", "template.docx", "copies/my_doc.docx")
        """
        from_path = _normalize_path(from_path)
        to_path = _normalize_path(to_path)
        
        try:
            self._get_bucket(bucket).copy(from_path, to_path)
        except Exception as e:
            raise StorageError(message=f"Failed to copy file: {e}")
    
    # =========================================================================
    # BUCKET MANAGEMENT (requires service_role_key)
    # =========================================================================
    
    async def create_bucket(
        self,
        name: str,
        *,
        public: bool = False,
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[List[str]] = None,
    ) -> Bucket:
        """
        Create a new storage bucket.
        
        Requires service_role_key.
        
        Args:
            name: Bucket name (lowercase, no spaces)
            public: Whether files are publicly accessible
            file_size_limit: Maximum file size in bytes
            allowed_mime_types: List of allowed MIME types
        
        Returns:
            Created Bucket
        
        Example:
            # Create public bucket for avatars
            bucket = await db.storage.create_bucket("avatars", public=True)
            
            # Create private bucket with restrictions
            bucket = await db.storage.create_bucket(
                "documents",
                public=False,
                file_size_limit=10 * 1024 * 1024,  # 10MB
                allowed_mime_types=["application/pdf", "image/*"]
            )
        """
        try:
            options = {
                "public": public,
            }
            if file_size_limit:
                options["file_size_limit"] = file_size_limit
            if allowed_mime_types:
                options["allowed_mime_types"] = allowed_mime_types
            
            response = self._client.create_bucket(name, options=options)
            
            return Bucket(
                id=name,
                name=name,
                public=public,
                file_size_limit=file_size_limit,
                allowed_mime_types=allowed_mime_types,
            )
            
        except Exception as e:
            raise StorageError(message=f"Failed to create bucket: {e}")
    
    async def get_bucket(self, name: str) -> Bucket:
        """
        Get bucket information.
        
        Args:
            name: Bucket name
        
        Returns:
            Bucket info
        
        Raises:
            BucketNotFoundError: If bucket doesn't exist
        """
        try:
            response = self._client.get_bucket(name)
            return Bucket.from_dict(response)
        except Exception as e:
            if "not found" in str(e).lower():
                raise BucketNotFoundError(bucket=name)
            raise StorageError(message=f"Failed to get bucket: {e}")
    
    async def list_buckets(self) -> List[Bucket]:
        """
        List all storage buckets.
        
        Returns:
            List of Bucket objects
        """
        try:
            response = self._client.list_buckets()
            return [Bucket.from_dict(b) for b in response]
        except Exception as e:
            raise StorageError(message=f"Failed to list buckets: {e}")
    
    async def update_bucket(
        self,
        name: str,
        *,
        public: Optional[bool] = None,
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[List[str]] = None,
    ) -> Bucket:
        """
        Update bucket settings.
        
        Requires service_role_key.
        
        Args:
            name: Bucket name
            public: New public setting
            file_size_limit: New file size limit
            allowed_mime_types: New allowed MIME types
        
        Returns:
            Updated Bucket
        """
        try:
            options = {}
            if public is not None:
                options["public"] = public
            if file_size_limit is not None:
                options["file_size_limit"] = file_size_limit
            if allowed_mime_types is not None:
                options["allowed_mime_types"] = allowed_mime_types
            
            response = self._client.update_bucket(name, options=options)
            return Bucket.from_dict(response) if isinstance(response, dict) else await self.get_bucket(name)
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise BucketNotFoundError(bucket=name)
            raise StorageError(message=f"Failed to update bucket: {e}")
    
    async def delete_bucket(self, name: str) -> None:
        """
        Delete an empty bucket.
        
        Requires service_role_key.
        Bucket must be empty before deletion.
        
        Args:
            name: Bucket name
        
        Raises:
            BucketNotFoundError: If bucket doesn't exist
            StorageError: If bucket is not empty
        """
        try:
            self._client.delete_bucket(name)
        except Exception as e:
            if "not found" in str(e).lower():
                raise BucketNotFoundError(bucket=name)
            raise StorageError(message=f"Failed to delete bucket: {e}")
    
    async def empty_bucket(self, name: str) -> None:
        """
        Delete all files in a bucket.
        
        Requires service_role_key.
        
        Args:
            name: Bucket name
        """
        try:
            self._client.empty_bucket(name)
        except Exception as e:
            if "not found" in str(e).lower():
                raise BucketNotFoundError(bucket=name)
            raise StorageError(message=f"Failed to empty bucket: {e}")

