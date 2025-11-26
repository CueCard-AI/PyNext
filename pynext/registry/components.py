"""
Native component management for PyNext UI.

Handles copying ShadCN components from pynext.shadcn to user's project
for customization.
"""

from __future__ import annotations

import inspect
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Map of component names to their source modules
AVAILABLE_COMPONENTS: dict[str, dict] = {
    # Basic Components
    "button": {
        "module": "pynext.shadcn.button",
        "description": "A button component with variants: default, destructive, outline, secondary, ghost, link",
        "exports": ["Button"],
        "category": "basic",
    },
    "input": {
        "module": "pynext.shadcn.input",
        "description": "Text input, label, and textarea components",
        "exports": ["Input", "Label", "Textarea"],
        "category": "basic",
    },
    "badge": {
        "module": "pynext.shadcn.badge",
        "description": "Small status indicator with variants",
        "exports": ["Badge"],
        "category": "basic",
    },
    "avatar": {
        "module": "pynext.shadcn.avatar",
        "description": "User avatar with image and fallback support",
        "exports": ["Avatar", "AvatarImage", "AvatarFallback"],
        "category": "basic",
    },
    "separator": {
        "module": "pynext.shadcn.separator",
        "description": "Visual divider for content separation",
        "exports": ["Separator"],
        "category": "basic",
    },
    
    # Card Components
    "card": {
        "module": "pynext.shadcn.card",
        "description": "Container for grouped content with header, content, and footer",
        "exports": ["Card", "CardHeader", "CardTitle", "CardDescription", "CardContent", "CardFooter"],
        "category": "card",
    },
    
    # Feedback Components
    "alert": {
        "module": "pynext.shadcn.alert",
        "description": "Alert message with title and description",
        "exports": ["Alert", "AlertTitle", "AlertDescription"],
        "category": "feedback",
    },
    "alert-dialog": {
        "module": "pynext.shadcn.alert_dialog",
        "description": "Modal dialog for important confirmations",
        "exports": [
            "AlertDialog", "AlertDialogTrigger", "AlertDialogContent",
            "AlertDialogHeader", "AlertDialogTitle", "AlertDialogDescription",
            "AlertDialogFooter", "AlertDialogAction", "AlertDialogCancel"
        ],
        "category": "feedback",
    },
    
    # Interactive Components
    "dialog": {
        "module": "pynext.shadcn.dialog",
        "description": "General purpose modal dialog",
        "exports": [
            "Dialog", "DialogTrigger", "DialogContent", "DialogHeader",
            "DialogTitle", "DialogDescription", "DialogFooter", "DialogClose"
        ],
        "category": "interactive",
    },
    "dropdown-menu": {
        "module": "pynext.shadcn.dropdown_menu",
        "description": "Dropdown menu with items, separators, and labels",
        "exports": [
            "DropdownMenu", "DropdownMenuTrigger", "DropdownMenuContent",
            "DropdownMenuItem", "DropdownMenuSeparator", "DropdownMenuLabel"
        ],
        "category": "interactive",
    },
    "tabs": {
        "module": "pynext.shadcn.tabs",
        "description": "Tabbed interface for organizing content",
        "exports": ["Tabs", "TabsList", "TabsTrigger", "TabsContent"],
        "category": "interactive",
    },
    "accordion": {
        "module": "pynext.shadcn.accordion",
        "description": "Collapsible content sections",
        "exports": ["Accordion", "AccordionItem", "AccordionTrigger", "AccordionContent"],
        "category": "interactive",
    },
    
    # Form Components
    "toggle": {
        "module": "pynext.shadcn.toggle",
        "description": "Toggle button with on/off state",
        "exports": ["Toggle", "ToggleGroup"],
        "category": "form",
    },
    "switch": {
        "module": "pynext.shadcn.switch",
        "description": "Switch toggle for boolean settings",
        "exports": ["Switch"],
        "category": "form",
    },
    "checkbox": {
        "module": "pynext.shadcn.checkbox",
        "description": "Checkbox input with label support",
        "exports": ["Checkbox"],
        "category": "form",
    },
    "radio-group": {
        "module": "pynext.shadcn.radio_group",
        "description": "Radio button group for single selection",
        "exports": ["RadioGroup", "RadioGroupItem"],
        "category": "form",
    },
}


@dataclass
class ComponentInfo:
    """Information about an available component."""
    name: str
    module: str
    description: str
    exports: list[str]
    category: str


def list_available_components(category: Optional[str] = None) -> list[ComponentInfo]:
    """
    List all available components.
    
    Args:
        category: Optional filter by category (basic, card, feedback, interactive, form)
    
    Returns:
        List of ComponentInfo objects
    """
    components = []
    for name, info in AVAILABLE_COMPONENTS.items():
        if category and info["category"] != category:
            continue
        components.append(ComponentInfo(
            name=name,
            module=info["module"],
            description=info["description"],
            exports=info["exports"],
            category=info["category"],
        ))
    return components


def get_component_source(component_name: str) -> Optional[str]:
    """
    Get the source code of a component.
    
    Args:
        component_name: Name of the component (e.g., "button", "card")
    
    Returns:
        Source code as string, or None if not found
    """
    if component_name not in AVAILABLE_COMPONENTS:
        return None
    
    info = AVAILABLE_COMPONENTS[component_name]
    module_name = info["module"]
    
    # Convert module name to file path
    # pynext.shadcn.button -> pynext/shadcn/button.py
    parts = module_name.split(".")
    
    # Find the pynext package location
    import pynext
    pynext_root = Path(pynext.__file__).parent
    
    # Build path to the component file
    relative_path = Path(*parts[1:])  # Skip 'pynext'
    file_path = pynext_root / f"{relative_path}.py"
    
    if file_path.exists():
        return file_path.read_text()
    
    return None


def copy_component_to_project(
    component_name: str,
    project_dir: Path,
    output_subdir: str = "components/ui",
) -> Optional[Path]:
    """
    Copy a component to the user's project for customization.
    
    Args:
        component_name: Name of the component (e.g., "button")
        project_dir: Root directory of the user's project
        output_subdir: Subdirectory to copy to (default: components/ui)
    
    Returns:
        Path to the copied file, or None if failed
    """
    source = get_component_source(component_name)
    if source is None:
        return None
    
    # Create output directory
    output_dir = project_dir / output_subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine output filename
    # Handle hyphenated names: alert-dialog -> alert_dialog.py
    filename = component_name.replace("-", "_") + ".py"
    output_path = output_dir / filename
    
    # Modify imports to work from user's project
    modified_source = _rewrite_imports(source, component_name)
    
    # Write the file
    output_path.write_text(modified_source)
    
    # Also create __init__.py if it doesn't exist
    init_path = output_dir / "__init__.py"
    if not init_path.exists():
        init_path.write_text('"""UI Components - copied from pynext.shadcn for customization."""\n')
    
    # Update __init__.py to include this component
    _update_init_file(init_path, component_name, AVAILABLE_COMPONENTS[component_name]["exports"])
    
    return output_path


def _rewrite_imports(source: str, component_name: str) -> str:
    """
    Rewrite imports in copied component to work from user's project.
    
    Changes:
    - from pynext.core.html import ... -> from pynext.core.html import ...  (keep)
    - from pynext.tw import ... -> from pynext.tw import ...  (keep)
    - from pynext.shadcn.primitives import ... -> from .primitives import ...  (relative)
    """
    lines = source.split("\n")
    new_lines = []
    
    for line in lines:
        # Rewrite shadcn primitive imports to relative
        if "from pynext.shadcn.primitives" in line:
            # from pynext.shadcn.primitives import X -> from .primitives import X
            line = line.replace("from pynext.shadcn.primitives", "from .primitives")
        
        new_lines.append(line)
    
    # Add header comment
    header = f'''"""
{component_name.title().replace("-", " ")} Component

Copied from pynext.shadcn for customization.
Edit this file to modify the component's appearance or behavior.

Original: pynext.shadcn.{component_name.replace("-", "_")}
"""

'''
    
    return header + "\n".join(new_lines)


def _update_init_file(init_path: Path, component_name: str, exports: list[str]) -> None:
    """Update __init__.py to export the new component."""
    content = init_path.read_text()
    
    # Create import line
    module_name = component_name.replace("-", "_")
    import_line = f"from .{module_name} import {', '.join(exports)}"
    
    # Check if already imported
    if import_line in content:
        return
    
    # Add import after docstring
    if content.startswith('"""'):
        # Find end of docstring
        end_docstring = content.find('"""', 3) + 3
        content = content[:end_docstring] + f"\n\n{import_line}" + content[end_docstring:]
    else:
        content = import_line + "\n" + content
    
    init_path.write_text(content)


def copy_all_components(
    project_dir: Path,
    output_subdir: str = "components/ui",
) -> list[Path]:
    """
    Copy all available components to the project.
    
    Args:
        project_dir: Root directory of the user's project
        output_subdir: Subdirectory to copy to
    
    Returns:
        List of paths to copied files
    """
    copied = []
    for name in AVAILABLE_COMPONENTS:
        result = copy_component_to_project(name, project_dir, output_subdir)
        if result:
            copied.append(result)
    
    # Also copy primitives
    _copy_primitives(project_dir, output_subdir)
    
    return copied


def _copy_primitives(project_dir: Path, output_subdir: str) -> None:
    """Copy primitive components needed by other components."""
    import pynext
    pynext_root = Path(pynext.__file__).parent
    
    primitives_src = pynext_root / "shadcn" / "primitives"
    primitives_dst = project_dir / output_subdir / "primitives"
    
    if primitives_src.exists():
        if primitives_dst.exists():
            shutil.rmtree(primitives_dst)
        shutil.copytree(primitives_src, primitives_dst)

