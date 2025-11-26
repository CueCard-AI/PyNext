# FileUpload

> **Like a drop zone for files — drag and drop or click to upload**

A component for selecting and uploading files with drag-and-drop support.

---

## First Principles: What IS a FileUpload?

### The Core Concept

A FileUpload provides **visual feedback** for file selection:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THE FILEUPLOAD CONCEPT                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  IDLE STATE:                                                                 │
│  ───────────                                                                │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │                                                             │            │
│  │            📁                                               │            │
│  │                                                             │            │
│  │     Drag and drop files here, or click to browse           │            │
│  │                                                             │            │
│  │     Accepted: .jpg, .png, .pdf (max 5MB)                   │            │
│  │                                                             │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                              │
│  DRAGGING STATE:                                                             │
│  ───────────────                                                            │
│  ┌═════════════════════════════════════════════════════════════┐            │
│  ║                                                             ║            │
│  ║            📁                                               ║            │
│  ║                                                             ║            │
│  ║              Drop files to upload                          ║            │
│  ║                                                             ║            │
│  └═════════════════════════════════════════════════════════════┘            │
│       ↑ Border highlights when dragging over                                │
│                                                                              │
│  WITH FILES:                                                                 │
│  ───────────                                                                │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │  📄 document.pdf          2.3 MB   ✓ Uploaded    [✕]       │            │
│  │  📸 photo.jpg             1.1 MB   ██████░░░ 60%           │            │
│  │  📄 report.pdf            5.2 MB   ✗ Too large   [↺]       │            │
│  └─────────────────────────────────────────────────────────────┘            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### File States

```
PENDING:     Queued for upload
UPLOADING:   Currently uploading (show progress)
SUCCESS:     Upload complete ✓
ERROR:       Upload failed (show reason)
```

---

## Installation

```bash
pynext ui add file-upload
```

Or import directly:

```python
from pynext.shadcn import FileUpload, FileUploadTrigger, FileUploadDropzone, FileUploadList
```

---

## Step-by-Step Usage

### Step 1: Basic File Upload

```python
from pynext import Signal

files = Signal([])

FileUpload(
    files=files.value,
    on_files_change=files.set,
    accept=".jpg,.png,.pdf",
    max_size=5 * 1024 * 1024  # 5MB
)[
    FileUploadDropzone()[
        Icons.upload(class_="h-8 w-8 text-muted-foreground"),
        p(class_="text-sm text-muted-foreground")[
            "Drag and drop or click to upload"
        ]
    ],
    FileUploadList()
]
```

### Step 2: With Server Upload

```python
from pynext import server_action

@server_action
async def upload_file(file: bytes, filename: str):
    path = f"uploads/{filename}"
    await storage.save(path, file)
    return {"url": f"/files/{path}"}

FileUpload(
    on_upload=upload_file,
    accept="image/*",
    max_files=5
)[
    FileUploadDropzone()[
        "Drop images here"
    ],
    FileUploadList()
]
```

### Step 3: Custom Styling

```python
FileUpload(files=files.value, on_files_change=files.set)[
    FileUploadDropzone(
        class_="border-2 border-dashed border-muted-foreground/25 rounded-lg p-12 hover:border-primary transition-colors"
    )[
        div(class_="flex flex-col items-center gap-2")[
            div(class_="rounded-full bg-primary/10 p-4")[
                Icons.cloud_upload(class_="h-8 w-8 text-primary")
            ],
            p(class_="font-medium")["Upload files"],
            p(class_="text-sm text-muted-foreground")[
                "Drag and drop or click to browse"
            ]
        ]
    ]
]
```

---

## Common Patterns

### Pattern 1: Avatar Upload

```python
div(class_="flex items-center gap-4")[
    Avatar(class_="h-20 w-20")[
        AvatarImage(src=avatar_url.value),
        AvatarFallback()["JD"]
    ],
    FileUpload(
        accept="image/*",
        max_files=1,
        on_upload=upload_avatar
    )[
        FileUploadTrigger()[
            Button(variant="outline")["Change avatar"]
        ]
    ]
]
```

### Pattern 2: Document Upload with Preview

```python
FileUpload(
    files=documents.value,
    on_files_change=documents.set,
    accept=".pdf,.doc,.docx"
)[
    FileUploadDropzone(class_="min-h-[200px]")[
        Icons.file_text(class_="h-10 w-10 text-muted-foreground"),
        p()["Drop documents here"]
    ],
    
    documents.value and div(class_="mt-4 space-y-2")[
        [
            div(class_="flex items-center justify-between p-3 border rounded-lg", key=f.name)[
                div(class_="flex items-center gap-3")[
                    Icons.file(class_="h-5 w-5"),
                    div()[
                        p(class_="font-medium")[f.name],
                        p(class_="text-xs text-muted-foreground")[
                            format_file_size(f.size)
                        ]
                    ]
                ],
                Button(
                    variant="ghost",
                    size="icon",
                    on_click=lambda f=f: remove_file(f)
                )[Icons.x()]
            ]
            for f in documents.value
        ]
    ]
]
```

### Pattern 3: Image Gallery Upload

```python
FileUpload(
    accept="image/*",
    max_files=10,
    on_upload=upload_image
)[
    div(class_="grid grid-cols-4 gap-4")[
        # Existing images
        [
            div(class_="relative aspect-square", key=img.id)[
                img(src=img.url, class_="rounded-lg object-cover w-full h-full"),
                Button(
                    variant="destructive",
                    size="icon",
                    class_="absolute top-2 right-2 h-6 w-6",
                    on_click=lambda i=img: delete_image(i.id)
                )[Icons.x(class_="h-4 w-4")]
            ]
            for img in images
        ],
        
        # Upload trigger
        FileUploadTrigger()[
            div(class_="aspect-square border-2 border-dashed rounded-lg flex items-center justify-center cursor-pointer hover:border-primary")[
                Icons.plus(class_="h-8 w-8 text-muted-foreground")
            ]
        ]
    ]
]
```

---

## API Reference

### FileUpload

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `accept` | str | `"*"` | Accepted file types |
| `max_size` | int | `None` | Max file size in bytes |
| `max_files` | int | `None` | Max number of files |
| `multiple` | bool | `True` | Allow multiple files |
| `disabled` | bool | `False` | Disable upload |
| `on_upload` | callable | `None` | Upload handler |
| `on_files_change` | callable | `None` | Called when files change |

### FileUploadDropzone

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `class_` | str | `""` | Custom styling |

---

## Validation

```python
FileUpload(
    accept=".pdf,.doc,.docx",           # File types
    max_size=10 * 1024 * 1024,          # 10MB max
    max_files=5,                         # Max 5 files
    validate=lambda f: (                 # Custom validation
        True if f.size < 10_000_000 
        else "File too large"
    )
)
```

---

## Accessibility

| Feature | Implementation |
|---------|----------------|
| **Keyboard** | Enter/Space to open file dialog |
| **Drop Zone** | `role="button"` with aria-label |
| **Progress** | Announced to screen readers |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Files not uploading | Missing on_upload | Add upload handler |
| Wrong file types | accept not set | Add accept prop |
| Large files failing | max_size limit | Increase or show error |

---

## Related Components

- **[Button](./button.md)** — For upload triggers
- **[Progress](./progress.md)** — For upload progress
