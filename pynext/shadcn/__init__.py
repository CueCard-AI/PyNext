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
]

