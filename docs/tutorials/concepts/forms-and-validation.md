# Forms & Validation

> **Build robust forms with server actions and validation**

Learn how to create forms in PyNext that handle user input, validate data, show errors, and submit to the server.

---

## What You'll Learn

- Creating forms with PyNext components
- Server actions for form handling
- Client-side validation with HTML5
- Server-side validation with Python
- Displaying validation errors
- Form state management

---

## Basic Form Structure

Every form in PyNext follows this pattern:

```python
from pynext import form, server_action
from pynext.shadcn import Button, Input, Label

@server_action
async def handle_submit(data: dict):
    """Process form data on the server."""
    name = data.get("name")
    email = data.get("email")
    
    # Validate and process
    return {"success": True}

def ContactForm():
    return form(action=handle_submit)[
        div(class_="space-y-4")[
            div(class_="space-y-2")[
                Label(html_for="name")["Name"],
                Input(id="name", name="name", required=True),
            ],
            div(class_="space-y-2")[
                Label(html_for="email")["Email"],
                Input(id="email", name="email", type="email", required=True),
            ],
            Button(type="submit")["Submit"],
        ],
    ]
```

**How it works:**
1. `form(action=handle_submit)` - Submits to server action
2. `name="field_name"` - Field names become keys in `data` dict
3. `@server_action` - Runs on server with full Python access
4. Returns result that can update the UI

---

## HTML5 Client-Side Validation

Use built-in browser validation for instant feedback:

```python
# Required field
Input(name="username", required=True)

# Email format
Input(name="email", type="email", required=True)

# Minimum length
Input(name="password", type="password", minlength=8)

# Pattern matching
Input(name="phone", pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}", 
      placeholder="123-456-7890")

# Number range
Input(name="age", type="number", min=18, max=120)

# URL format
Input(name="website", type="url")
```

### Custom Validation Messages

```python
Input(
    name="username",
    required=True,
    pattern="[a-z0-9_]+",
    title="Only lowercase letters, numbers, and underscores",
)
```

---

## Server-Side Validation

Always validate on the server — client validation can be bypassed:

```python
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ValidationError:
    field: str
    message: str

def validate_user(data: dict) -> List[ValidationError]:
    """Validate user registration data."""
    errors = []
    
    # Required fields
    if not data.get("name"):
        errors.append(ValidationError("name", "Name is required"))
    
    if not data.get("email"):
        errors.append(ValidationError("email", "Email is required"))
    elif "@" not in data["email"]:
        errors.append(ValidationError("email", "Invalid email format"))
    
    # Password strength
    password = data.get("password", "")
    if len(password) < 8:
        errors.append(ValidationError("password", "Password must be at least 8 characters"))
    elif not any(c.isupper() for c in password):
        errors.append(ValidationError("password", "Password must contain uppercase letter"))
    
    return errors


@server_action
async def register_user(data: dict):
    """Register a new user with validation."""
    errors = validate_user(data)
    
    if errors:
        return {
            "success": False,
            "errors": {e.field: e.message for e in errors},
        }
    
    # Process valid data
    # ... save to database ...
    
    return {"success": True, "message": "Account created!"}
```

---

## Displaying Validation Errors

Create a reusable form field component with error display:

```python
from pynext import Signal

def FormField(
    name: str,
    label: str,
    type: str = "text",
    error: str = None,
    **props,
):
    """Form field with label and error display."""
    return div(class_="space-y-2")[
        Label(html_for=name)[
            label,
            props.get("required") and span(class_="text-destructive ml-1")["*"],
        ],
        Input(
            id=name,
            name=name,
            type=type,
            class_=cn(
                error and "border-destructive focus:ring-destructive",
            ),
            aria_invalid="true" if error else None,
            aria_describedby=f"{name}-error" if error else None,
            **props,
        ),
        error and p(
            id=f"{name}-error",
            class_="text-sm text-destructive",
        )[error],
    ]
```

### Using with Server Response

```python
form_errors = Signal({})

@server_action
async def submit_form(data: dict):
    errors = validate_data(data)
    if errors:
        form_errors.set(errors)
        return {"success": False}
    return {"success": True}

def MyForm():
    errors = form_errors.value
    
    return form(action=submit_form)[
        FormField(
            name="email",
            label="Email",
            type="email",
            error=errors.get("email"),
            required=True,
        ),
        FormField(
            name="password",
            label="Password",
            type="password",
            error=errors.get("password"),
            required=True,
        ),
        Button(type="submit")["Submit"],
    ]
```

---

## Form State Patterns

### Loading State

```python
is_submitting = Signal(False)

@server_action
async def submit_form(data: dict):
    is_submitting.set(True)
    try:
        # Process form...
        await save_data(data)
        return {"success": True}
    finally:
        is_submitting.set(False)

def SubmitButton():
    return Button(
        type="submit",
        disabled=is_submitting.value,
    )[
        is_submitting.value and span(class_="mr-2")["⏳"],
        "Saving..." if is_submitting.value else "Save",
    ]
```

### Success Message

```python
show_success = Signal(False)

@server_action
async def submit_form(data: dict):
    # Save data...
    show_success.set(True)
    return {"success": True}

def Form():
    return div()[
        show_success.value and Alert(class_="mb-4")[
            AlertTitle()["Success!"],
            AlertDescription()["Your changes have been saved."],
        ],
        form(action=submit_form)[
            # ... fields ...
        ],
    ]
```

---

## Multi-Step Forms

```python
current_step = Signal(1)

def MultiStepForm():
    step = current_step.value
    
    return div()[
        # Progress indicator
        div(class_="flex gap-2 mb-6")[
            StepIndicator(1, "Account", step),
            StepIndicator(2, "Profile", step),
            StepIndicator(3, "Confirm", step),
        ],
        
        # Step content
        step == 1 and AccountStep(),
        step == 2 and ProfileStep(),
        step == 3 and ConfirmStep(),
        
        # Navigation
        div(class_="flex justify-between mt-6")[
            step > 1 and Button(
                variant="outline",
                onclick=lambda: current_step.update(lambda s: s - 1),
            )["Back"],
            step < 3 and Button(
                onclick=lambda: current_step.update(lambda s: s + 1),
            )["Next"],
            step == 3 and Button(type="submit")["Submit"],
        ],
    ]
```

---

## File Uploads

```python
@server_action
async def upload_file(data: dict):
    file = data.get("file")
    if not file:
        return {"success": False, "error": "No file provided"}
    
    # In a real app, save to storage
    # file.filename, file.content_type, file.read()
    
    return {"success": True, "filename": file.filename}

def FileUploadForm():
    return form(action=upload_file, enctype="multipart/form-data")[
        div(class_="space-y-4")[
            Label(html_for="file")["Upload File"],
            Input(
                id="file",
                name="file",
                type="file",
                accept=".pdf,.doc,.docx",
            ),
            Button(type="submit")["Upload"],
        ],
    ]
```

---

## Complete Example: Registration Form

```python
from pynext import page, server_action, Signal, div, form, h1, p
from pynext.shadcn import Button, Input, Label, Checkbox, Alert, AlertTitle

# State
errors = Signal({})
success = Signal(False)
loading = Signal(False)


@server_action
async def register(data: dict):
    loading.set(True)
    errors.set({})
    
    # Validate
    validation_errors = {}
    
    if not data.get("name"):
        validation_errors["name"] = "Name is required"
    
    email = data.get("email", "")
    if not email:
        validation_errors["email"] = "Email is required"
    elif "@" not in email:
        validation_errors["email"] = "Invalid email format"
    
    password = data.get("password", "")
    if len(password) < 8:
        validation_errors["password"] = "Password must be at least 8 characters"
    
    if data.get("password") != data.get("confirm_password"):
        validation_errors["confirm_password"] = "Passwords do not match"
    
    if not data.get("terms"):
        validation_errors["terms"] = "You must accept the terms"
    
    if validation_errors:
        errors.set(validation_errors)
        loading.set(False)
        return {"success": False}
    
    # Save user (in real app)
    # await create_user(data)
    
    loading.set(False)
    success.set(True)
    return {"success": True}


@page(title="Register")
def register_page():
    if success.value:
        return div(class_="max-w-md mx-auto p-8")[
            Alert()[
                AlertTitle()["Account Created!"],
                p()["Check your email to verify your account."],
            ],
        ]
    
    errs = errors.value
    
    return div(class_="max-w-md mx-auto p-8")[
        h1(class_="text-2xl font-bold mb-6")["Create Account"],
        
        form(action=register, class_="space-y-4")[
            # Name
            div(class_="space-y-2")[
                Label(html_for="name")["Name *"],
                Input(id="name", name="name", required=True,
                      class_=errs.get("name") and "border-destructive"),
                errs.get("name") and p(class_="text-sm text-destructive")[errs["name"]],
            ],
            
            # Email
            div(class_="space-y-2")[
                Label(html_for="email")["Email *"],
                Input(id="email", name="email", type="email", required=True,
                      class_=errs.get("email") and "border-destructive"),
                errs.get("email") and p(class_="text-sm text-destructive")[errs["email"]],
            ],
            
            # Password
            div(class_="space-y-2")[
                Label(html_for="password")["Password *"],
                Input(id="password", name="password", type="password", 
                      minlength=8, required=True,
                      class_=errs.get("password") and "border-destructive"),
                errs.get("password") and p(class_="text-sm text-destructive")[errs["password"]],
            ],
            
            # Confirm Password
            div(class_="space-y-2")[
                Label(html_for="confirm")["Confirm Password *"],
                Input(id="confirm", name="confirm_password", type="password", required=True,
                      class_=errs.get("confirm_password") and "border-destructive"),
                errs.get("confirm_password") and p(class_="text-sm text-destructive")[errs["confirm_password"]],
            ],
            
            # Terms
            div(class_="flex items-center gap-2")[
                Checkbox(id="terms", name="terms", required=True),
                Label(html_for="terms", class_="text-sm")[
                    "I agree to the Terms of Service"
                ],
            ],
            errs.get("terms") and p(class_="text-sm text-destructive")[errs["terms"]],
            
            # Submit
            Button(type="submit", class_="w-full", disabled=loading.value)[
                "Creating Account..." if loading.value else "Create Account"
            ],
        ],
    ]
```

---

## Key Takeaways

1. **Always validate server-side** — Client validation is for UX only
2. **Use HTML5 validation** — Free instant feedback
3. **Show clear errors** — Next to the field that needs fixing
4. **Handle loading states** — Prevent double submission
5. **Use server actions** — Full Python power for processing

---

## Related Tutorials

- [State Management](./state-management.md) - Managing form state
- [Data Tables](./data-tables.md) - Displaying submitted data
- [Authentication](./authentication.md) - Login/signup forms

