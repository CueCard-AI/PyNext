"""
Runtime Bundling for PyNext

Analyzes Python source to determine which runtime modules are needed,
then bundles only those modules.
"""

import ast
import os
from pathlib import Path
from typing import Set, List, Optional


# Map Python imports/decorators to required JS runtime files
FEATURE_TO_RUNTIME = {
    # Client primitives
    'on_keydown': 'keyboard.js',
    'on_key_sequence': 'keyboard.js',
    'register_shortcut': 'keyboard.js',
    'use_storage': 'storage.js',
    'use_theme': 'theme.js',
    'use_visibility': 'browser.js',
    'use_online': 'browser.js',
    'use_event_source': 'sse.js',
    'client_effect': 'signals.js',
    'use_ref': 'signals.js',
    
    # Focus management
    'FocusTrap': 'focus.js',
    'RovingFocus': 'focus.js',
    'SkipLinks': 'focus.js',
    
    # Theme components
    'ThemeProvider': 'theme.js',
    'ThemeToggle': 'theme.js',
    'ThemeScript': 'theme.js',
    
    # Keyboard components
    'ShortcutProvider': 'keyboard.js',
    'ShortcutHint': 'keyboard.js',
    'ShortcutsHelpDialog': 'keyboard.js',
}

# Map ShadCN components to UI runtime modules
COMPONENT_TO_UI_MODULE = {
    'Dialog': 'ui/dialog.js',
    'DialogTrigger': 'ui/dialog.js',
    'DialogContent': 'ui/dialog.js',
    'AlertDialog': 'ui/dialog.js',
    'DropdownMenu': 'ui/dropdown.js',
    'DropdownMenuTrigger': 'ui/dropdown.js',
    'Tabs': 'ui/tabs.js',
    'TabsList': 'ui/tabs.js',
    'TabsTrigger': 'ui/tabs.js',
    'Accordion': 'ui/accordion.js',
    'AccordionItem': 'ui/accordion.js',
    'Switch': 'ui/forms.js',
    'Checkbox': 'ui/forms.js',
    'Toggle': 'ui/forms.js',
    'ToggleGroup': 'ui/forms.js',
    'RadioGroup': 'ui/forms.js',
    'Tooltip': 'ui/tooltip.js',
    'TooltipTrigger': 'ui/tooltip.js',
    'Popover': 'ui/popover.js',
    'PopoverTrigger': 'ui/popover.js',
    'Sheet': 'ui/sheet.js',
    'SheetTrigger': 'ui/sheet.js',
    'Combobox': 'ui/combobox.js',
    'ComboboxTrigger': 'ui/combobox.js',
    'Command': 'ui/command.js',
    'CommandInput': 'ui/command.js',
    'Calendar': 'ui/calendar.js',
    'DatePicker': 'ui/calendar.js',
    'DataTable': 'ui/datatable.js',
    'FileUpload': 'ui/fileupload.js',
}


class ImportAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST to find PyNext imports."""
    
    def __init__(self):
        self.imports: Set[str] = set()
        self.from_imports: Set[str] = set()
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module and node.module.startswith('pynext'):
            for alias in node.names:
                self.from_imports.add(alias.name)
        self.generic_visit(node)


def analyze_file(file_path: Path) -> Set[str]:
    """
    Analyze a Python file to find required runtime modules.
    
    Args:
        file_path: Path to Python file
    
    Returns:
        Set of required runtime module names
    """
    try:
        source = file_path.read_text()
        tree = ast.parse(source)
    except (SyntaxError, FileNotFoundError):
        return set()
    
    analyzer = ImportAnalyzer()
    analyzer.visit(tree)
    
    required = set()
    
    # Check feature imports
    for name in analyzer.from_imports:
        if name in FEATURE_TO_RUNTIME:
            required.add(FEATURE_TO_RUNTIME[name])
        if name in COMPONENT_TO_UI_MODULE:
            required.add(COMPONENT_TO_UI_MODULE[name])
            required.add('ui/core.js')  # Core is always needed for UI
    
    return required


def analyze_directory(dir_path: Path) -> Set[str]:
    """
    Analyze all Python files in a directory.
    
    Args:
        dir_path: Directory to analyze
    
    Returns:
        Set of required runtime module names
    """
    required = set()
    
    for py_file in dir_path.rglob('*.py'):
        required.update(analyze_file(py_file))
    
    return required


def get_required_modules(app_dir: Path) -> List[str]:
    """
    Get list of required runtime modules for an app.
    
    Args:
        app_dir: Application directory (containing pages/, etc.)
    
    Returns:
        Sorted list of required module paths
    """
    required = analyze_directory(app_dir)
    
    # Always include signals (core reactivity)
    required.add('signals.js')
    
    return sorted(required)


def bundle_runtime(
    required_modules: List[str],
    runtime_dir: Optional[Path] = None,
    minified: bool = True,
) -> str:
    """
    Bundle required runtime modules into a single file.
    
    Args:
        required_modules: List of module names to include
        runtime_dir: Directory containing runtime files
        minified: Whether to use minified versions
    
    Returns:
        Bundled JavaScript code
    """
    if runtime_dir is None:
        runtime_dir = Path(__file__).parent.parent / 'runtime'
    
    if minified:
        runtime_dir = runtime_dir / 'min'
    
    parts = []
    loaded = set()
    
    # Add core if any UI modules are needed
    ui_modules = [m for m in required_modules if m.startswith('ui/')]
    if ui_modules and 'ui/core.js' not in loaded:
        core_path = runtime_dir / 'ui' / 'core.js'
        if core_path.exists():
            parts.append(core_path.read_text())
            loaded.add('ui/core.js')
    
    # Add each required module
    for module in required_modules:
        if module in loaded:
            continue
        
        module_path = runtime_dir / module
        if module_path.exists():
            parts.append(module_path.read_text())
            loaded.add(module)
    
    return '\n'.join(parts)

