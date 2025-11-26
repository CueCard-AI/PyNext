# FileUpload

A drag-and-drop file upload component with progress tracking.

## Installation

```python
from pynext.shadcn import (
    FileUpload, FileUploadDropzone, FileUploadTrigger,
    FileUploadList, FileUploadItem
)
```

## Basic Usage

```python
FileUpload(on_upload=handle_upload)[
    FileUploadDropzone()[
        "Drag and drop files here, or click to browse"
    ]
]
```

## Examples

### With File List

```python
FileUpload(on_upload=handle_upload, multiple=True)[
    FileUploadDropzone()[
        FileUploadTrigger()[
            Button()["Select Files"]
        ],
        p(class_="text-sm text-muted-foreground mt-2")[
            "or drag and drop"
        ]
    ],
    FileUploadList()[
        [FileUploadItem(
            file_name=f.name,
            file_size=f.size,
            progress=f.progress,
            status=f.status
        ) for f in uploaded_files]
    ]
]
```

### Image Upload with Preview

```python
FileUpload(
    accept="image/*",
    max_size=5 * 1024 * 1024,  # 5MB
    on_upload=upload_image
)[
    FileUploadDropzone(preview=True, size="lg")[
        "Drop your image here"
    ]
]
```

### Multiple Files with Limit

```python
FileUpload(
    multiple=True,
    max_files=5,
    max_size=10 * 1024 * 1024,  # 10MB per file
)[
    FileUploadDropzone()[
        "Upload up to 5 files (max 10MB each)"
    ]
]
```

### Accept Specific Types

```python
# Images only
FileUpload(accept="image/*")[...]

# Documents
FileUpload(accept=".pdf,.doc,.docx")[...]

# Specific MIME types
FileUpload(accept="image/png,image/jpeg")[...]
```

### Upload Progress

```python
FileUploadItem(
    file_name="document.pdf",
    file_size=1024 * 1024,  # 1MB
    progress=75,
    status="uploading"
)
```

### Different Statuses

```python
# Pending
FileUploadItem(file_name="file.pdf", status="pending")

# Uploading
FileUploadItem(file_name="file.pdf", status="uploading", progress=50)

# Complete
FileUploadItem(file_name="file.pdf", status="complete")

# Error
FileUploadItem(
    file_name="file.pdf",
    status="error",
    error_message="File too large"
)
```

## API Reference

### FileUpload

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `on_upload` | `Callable` | `None` | Upload callback |
| `accept` | `str` | `None` | Accepted file types |
| `multiple` | `bool` | `False` | Allow multiple files |
| `max_size` | `int` | `None` | Max file size (bytes) |
| `max_files` | `int` | `None` | Max number of files |
| `disabled` | `bool` | `False` | Disable upload |

### FileUploadDropzone

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `size` | `"sm" \| "md" \| "lg"` | `"md"` | Dropzone height |
| `preview` | `bool` | `False` | Show image previews |

### FileUploadItem

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `file_name` | `str` | required | File name |
| `file_size` | `int` | `0` | Size in bytes |
| `progress` | `int` | `0` | Upload progress (0-100) |
| `status` | `string` | `"pending"` | Current status |
| `preview_url` | `str` | `None` | Image preview URL |
| `error_message` | `str` | `None` | Error message |

## Events

```python
# File selection
@on("pynext:file-select")
def handle_select(event):
    files = event.detail.files
    for file in files:
        # Start upload
        upload(file)

# File removal
@on("pynext:file-remove")
def handle_remove(event):
    # Handle removal
    pass
```

## Server Integration

```python
@server_action
async def upload_file(file):
    # Read file content
    content = await file.read()
    
    # Save to storage
    path = await storage.save(file.filename, content)
    
    return {"url": path}
```

