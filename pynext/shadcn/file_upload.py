"""
File Upload Component

A drag-and-drop file upload component with progress tracking.

Usage:
    from pynext.shadcn import (
        FileUpload, FileUploadDropzone, FileUploadTrigger,
        FileUploadList, FileUploadItem
    )
    
    # Basic usage
    FileUpload(on_upload=handle_upload)[
        FileUploadDropzone()[
            "Drag and drop files here, or click to browse"
        ]
    ]
    
    # With file list
    FileUpload(on_upload=handle_upload, multiple=True)[
        FileUploadDropzone()[
            FileUploadTrigger()[
                Button()["Select Files"]
            ],
            p()["or drag and drop"]
        ],
        FileUploadList()[
            # Files rendered automatically
        ]
    ]
    
    # Image upload with preview
    FileUpload(
        accept="image/*",
        max_size=5 * 1024 * 1024,  # 5MB
        on_upload=upload_image
    )[
        FileUploadDropzone(preview=True)[...]
    ]
"""

from typing import Any, Optional, List, Union, Callable, Literal
from pynext.tw import cn
import hashlib


# Dropzone styles
DROPZONE_BASE = (
    "relative flex flex-col items-center justify-center w-full "
    "border-2 border-dashed rounded-lg cursor-pointer transition-colors "
    "hover:bg-accent/50 "
    "data-[drag-active=true]:border-primary data-[drag-active=true]:bg-primary/10"
)

DROPZONE_SIZES = {
    "sm": "h-32 px-4",
    "md": "h-48 px-6",
    "lg": "h-64 px-8",
}

# File list styles
FILE_LIST_BASE = "mt-4 space-y-2"

# File item styles
FILE_ITEM_BASE = (
    "flex items-center justify-between p-3 bg-muted/50 rounded-lg"
)

FILE_ITEM_INFO_BASE = "flex items-center space-x-3 overflow-hidden"
FILE_ITEM_ICON_BASE = "flex-shrink-0 w-10 h-10 rounded flex items-center justify-center bg-background"
FILE_ITEM_DETAILS_BASE = "min-w-0 flex-1"
FILE_ITEM_NAME_BASE = "text-sm font-medium truncate"
FILE_ITEM_SIZE_BASE = "text-xs text-muted-foreground"
FILE_ITEM_ACTIONS_BASE = "flex items-center space-x-2"

# Progress bar styles
PROGRESS_BASE = "w-full h-1.5 bg-muted rounded-full overflow-hidden"
PROGRESS_BAR_BASE = "h-full bg-primary transition-all duration-300"


class FileUpload:
    """
    Root component for file uploads.
    
    Attributes:
        on_upload: Callback when files are uploaded
        accept: Accepted file types (e.g., "image/*", ".pdf,.doc")
        multiple: Allow multiple file selection
        max_size: Maximum file size in bytes
        max_files: Maximum number of files
        disabled: Whether upload is disabled
        class_: Additional CSS classes
    
    Example:
        FileUpload(
            on_upload=handle_files,
            accept="image/*",
            multiple=True,
            max_size=5 * 1024 * 1024
        )[
            FileUploadDropzone()[...]
        ]
    """
    
    def __init__(
        self,
        on_upload: Optional[Callable[[List[Any]], None]] = None,
        accept: Optional[str] = None,
        multiple: bool = False,
        max_size: Optional[int] = None,
        max_files: Optional[int] = None,
        disabled: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.on_upload = on_upload
        self.accept = accept
        self.multiple = multiple
        self.max_size = max_size
        self.max_files = max_files
        self.disabled = disabled
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "FileUpload":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        upload_id = hashlib.md5(str(id(self)).encode()).hexdigest()[:8]
        
        attrs = [
            f'data-pynext-file-upload="{upload_id}"',
        ]
        if self.accept:
            attrs.append(f'data-accept="{self.accept}"')
        if self.multiple:
            attrs.append('data-multiple="true"')
        if self.max_size:
            attrs.append(f'data-max-size="{self.max_size}"')
        if self.max_files:
            attrs.append(f'data-max-files="{self.max_files}"')
        if self.disabled:
            attrs.append('data-disabled="true"')
        
        class_str = cn(self.extra_class) if self.extra_class else ""
        if class_str:
            attrs.append(f'class="{class_str}"')
        
        return f'''
<div {" ".join(attrs)}>
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class FileUploadDropzone:
    """
    The dropzone area for drag-and-drop uploads.
    
    Attributes:
        size: Size variant ("sm", "md", "lg")
        preview: Show image previews
        class_: Additional CSS classes
    
    Example:
        FileUploadDropzone(size="lg")[
            "Drop files here"
        ]
    """
    
    def __init__(
        self,
        size: Literal["sm", "md", "lg"] = "md",
        preview: bool = False,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.size = size
        self.preview = preview
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "FileUploadDropzone":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        size_class = DROPZONE_SIZES.get(self.size, DROPZONE_SIZES["md"])
        class_str = cn(DROPZONE_BASE, size_class, self.extra_class)
        
        preview_attr = 'data-preview="true"' if self.preview else ""
        
        # Upload icon
        upload_icon = '''
<svg class="w-10 h-10 mb-3 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
</svg>
'''
        
        return f'''
<label data-pynext-dropzone {preview_attr} class="{class_str}">
    <input type="file" 
           data-pynext-file-input
           class="sr-only" />
    {upload_icon}
    <div class="text-center">
        {children_html}
    </div>
</label>
'''
    
    def __str__(self) -> str:
        return self.render()


class FileUploadTrigger:
    """
    A button trigger for file selection.
    
    Example:
        FileUploadTrigger()[
            Button()["Choose Files"]
        ]
    """
    
    def __init__(self, **attrs: Any):
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "FileUploadTrigger":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        return f'''
<div data-pynext-file-trigger style="display:contents">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class FileUploadList:
    """
    Container for displaying uploaded files.
    
    Example:
        FileUploadList()[
            FileUploadItem(file=file) for file in files
        ]
    """
    
    def __init__(self, class_: Optional[str] = None, **attrs: Any):
        self.extra_class = class_
        self.attrs = attrs
        self._children: List[Any] = []
    
    def __getitem__(self, children: Union[Any, tuple]) -> "FileUploadList":
        if isinstance(children, tuple):
            self._children = list(children)
        else:
            self._children = [children]
        return self
    
    def render(self) -> str:
        children_html = "".join(
            child.render() if hasattr(child, 'render') else str(child)
            for child in self._children
        )
        
        class_str = cn(FILE_LIST_BASE, self.extra_class)
        
        return f'''
<div data-pynext-file-list class="{class_str}">
    {children_html}
</div>
'''
    
    def __str__(self) -> str:
        return self.render()


class FileUploadItem:
    """
    A single file item in the upload list.
    
    Attributes:
        file_name: Name of the file
        file_size: Size in bytes
        file_type: MIME type
        progress: Upload progress (0-100)
        preview_url: URL for image preview
        on_remove: Callback when remove is clicked
        status: "pending", "uploading", "complete", "error"
    
    Example:
        FileUploadItem(
            file_name="document.pdf",
            file_size=1024 * 1024,
            progress=75,
            status="uploading"
        )
    """
    
    def __init__(
        self,
        file_name: str,
        file_size: int = 0,
        file_type: Optional[str] = None,
        progress: int = 0,
        preview_url: Optional[str] = None,
        on_remove: Optional[Callable] = None,
        status: Literal["pending", "uploading", "complete", "error"] = "pending",
        error_message: Optional[str] = None,
        class_: Optional[str] = None,
        **attrs: Any
    ):
        self.file_name = file_name
        self.file_size = file_size
        self.file_type = file_type
        self.progress = progress
        self.preview_url = preview_url
        self.on_remove = on_remove
        self.status = status
        self.error_message = error_message
        self.extra_class = class_
        self.attrs = attrs
    
    def render(self) -> str:
        class_str = cn(FILE_ITEM_BASE, self.extra_class)
        
        # Icon or preview
        icon_html = self._render_icon()
        
        # Size formatting
        size_str = self._format_size(self.file_size)
        
        # Progress bar (only when uploading)
        progress_html = ""
        if self.status == "uploading":
            progress_html = f'''
<div class="{cn(PROGRESS_BASE)} mt-2">
    <div class="{cn(PROGRESS_BAR_BASE)}" style="width:{self.progress}%"></div>
</div>
'''
        
        # Status indicator
        status_html = ""
        if self.status == "complete":
            status_html = '''
<svg class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
</svg>
'''
        elif self.status == "error":
            status_html = f'''
<div class="flex items-center text-red-500">
    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
    </svg>
    <span class="ml-1 text-xs">{self.error_message or "Error"}</span>
</div>
'''
        
        # Remove button
        remove_html = '''
<button type="button" 
        data-pynext-file-remove
        class="p-1 rounded-md hover:bg-muted"
        aria-label="Remove file">
    <svg class="w-4 h-4 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
    </svg>
</button>
'''
        
        return f'''
<div data-pynext-file-item data-status="{self.status}" class="{class_str}">
    <div class="{cn(FILE_ITEM_INFO_BASE)}">
        {icon_html}
        <div class="{cn(FILE_ITEM_DETAILS_BASE)}">
            <p class="{cn(FILE_ITEM_NAME_BASE)}">{self.file_name}</p>
            <p class="{cn(FILE_ITEM_SIZE_BASE)}">{size_str}</p>
            {progress_html}
        </div>
    </div>
    <div class="{cn(FILE_ITEM_ACTIONS_BASE)}">
        {status_html}
        {remove_html}
    </div>
</div>
'''
    
    def _render_icon(self) -> str:
        """Render file type icon or image preview."""
        if self.preview_url:
            return f'''
<div class="{cn(FILE_ITEM_ICON_BASE)} overflow-hidden">
    <img src="{self.preview_url}" alt="{self.file_name}" class="w-full h-full object-cover"/>
</div>
'''
        
        # Default file icon
        return f'''
<div class="{cn(FILE_ITEM_ICON_BASE)}">
    <svg class="w-5 h-5 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
    </svg>
</div>
'''
    
    def _format_size(self, bytes: int) -> str:
        """Format file size for display."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}" if bytes < 10 else f"{bytes:.0f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"
    
    def __str__(self) -> str:
        return self.render()

