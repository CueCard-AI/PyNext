"""
PyNext ShadCN Components

A full port of ShadCN/ui to PyNext, providing beautiful, accessible components
with identical APIs and Tailwind styling - but in pure Python.

Example:
    from pynext.shadcn import Button, Card, Dialog, Input
    
    Card()[
        CardHeader()[CardTitle()["Sign In"]],
        CardContent()[
            Input(placeholder="Email"),
            Input(type="password", placeholder="Password"),
            Button()["Continue"]
        ]
    ]
"""

# Basic Components
from .button import Button
from .input import Input, Label, Textarea
from .badge import Badge
from .avatar import Avatar, AvatarImage, AvatarFallback
from .separator import Separator

# Card Components
from .card import Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter

# Feedback Components
from .alert import Alert, AlertTitle, AlertDescription
from .alert_dialog import (
    AlertDialog, AlertDialogTrigger, AlertDialogContent,
    AlertDialogHeader, AlertDialogTitle, AlertDialogDescription,
    AlertDialogFooter, AlertDialogAction, AlertDialogCancel
)

# Interactive Components
from .dialog import (
    Dialog, DialogTrigger, DialogContent,
    DialogHeader, DialogTitle, DialogDescription, DialogFooter
)
from .dropdown_menu import (
    DropdownMenu, DropdownMenuTrigger, DropdownMenuContent,
    DropdownMenuItem, DropdownMenuSeparator, DropdownMenuLabel
)
from .tabs import Tabs, TabsList, TabsTrigger, TabsContent
from .accordion import Accordion, AccordionItem, AccordionTrigger, AccordionContent

# Form Components
from .toggle import Toggle, ToggleGroup
from .switch import Switch
from .checkbox import Checkbox
from .radio_group import RadioGroup, RadioGroupItem

# Phase 2 Components - Foundation
from .skeleton import Skeleton, SkeletonCard, SkeletonTable, SkeletonText
from .tooltip import Tooltip, TooltipTrigger, TooltipContent, TooltipProvider
from .popover import Popover, PopoverTrigger, PopoverContent, PopoverAnchor, PopoverClose
from .toast import Toaster, Toast, toast

# Phase 2 Components - Interactive
from .sheet import (
    Sheet, SheetTrigger, SheetContent, SheetHeader, SheetTitle,
    SheetDescription, SheetFooter, SheetClose
)
from .combobox import (
    Combobox, ComboboxTrigger, ComboboxContent, ComboboxInput,
    ComboboxItem, ComboboxEmpty, ComboboxGroup, ComboboxSeparator, ComboboxCreate
)

# Phase 3 Components - Complex
from .command import (
    Command, CommandDialog, CommandInput, CommandList, CommandEmpty,
    CommandGroup, CommandItem, CommandSeparator, CommandShortcut
)
from .calendar import Calendar
from .date_picker import DatePicker, DateRangePicker
from .data_table import (
    DataTable, DataTableColumn, DataTableToolbar,
    DataTableFacetedFilter, DataTablePagination, DataTableColumnToggle
)

# Phase 4 Components - External Integrations
from .file_upload import (
    FileUpload, FileUploadDropzone, FileUploadTrigger,
    FileUploadList, FileUploadItem
)

__all__ = [
    # Basic
    "Button",
    "Input", "Label", "Textarea",
    "Badge",
    "Avatar", "AvatarImage", "AvatarFallback",
    "Separator",
    
    # Card
    "Card", "CardHeader", "CardTitle", "CardDescription", "CardContent", "CardFooter",
    
    # Feedback
    "Alert", "AlertTitle", "AlertDescription",
    "AlertDialog", "AlertDialogTrigger", "AlertDialogContent",
    "AlertDialogHeader", "AlertDialogTitle", "AlertDialogDescription",
    "AlertDialogFooter", "AlertDialogAction", "AlertDialogCancel",
    
    # Interactive
    "Dialog", "DialogTrigger", "DialogContent",
    "DialogHeader", "DialogTitle", "DialogDescription", "DialogFooter",
    "DropdownMenu", "DropdownMenuTrigger", "DropdownMenuContent",
    "DropdownMenuItem", "DropdownMenuSeparator", "DropdownMenuLabel",
    "Tabs", "TabsList", "TabsTrigger", "TabsContent",
    "Accordion", "AccordionItem", "AccordionTrigger", "AccordionContent",
    
    # Form
    "Toggle", "ToggleGroup",
    "Switch",
    "Checkbox",
    "RadioGroup", "RadioGroupItem",
    
    # Phase 2 - Foundation
    "Skeleton", "SkeletonCard", "SkeletonTable", "SkeletonText",
    "Tooltip", "TooltipTrigger", "TooltipContent", "TooltipProvider",
    "Popover", "PopoverTrigger", "PopoverContent", "PopoverAnchor", "PopoverClose",
    "Toaster", "Toast", "toast",
    
    # Phase 2 - Interactive
    "Sheet", "SheetTrigger", "SheetContent", "SheetHeader", "SheetTitle",
    "SheetDescription", "SheetFooter", "SheetClose",
    "Combobox", "ComboboxTrigger", "ComboboxContent", "ComboboxInput",
    "ComboboxItem", "ComboboxEmpty", "ComboboxGroup", "ComboboxSeparator", "ComboboxCreate",
    
    # Phase 3 - Complex
    "Command", "CommandDialog", "CommandInput", "CommandList", "CommandEmpty",
    "CommandGroup", "CommandItem", "CommandSeparator", "CommandShortcut",
    "Calendar",
    "DatePicker", "DateRangePicker",
    "DataTable", "DataTableColumn", "DataTableToolbar",
    "DataTableFacetedFilter", "DataTablePagination", "DataTableColumnToggle",
    
    # Phase 4 - External Integrations
    "FileUpload", "FileUploadDropzone", "FileUploadTrigger",
    "FileUploadList", "FileUploadItem",
]

