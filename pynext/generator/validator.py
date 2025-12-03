"""
Code Validator for AI-Generated PyNext Code.

Validates generated code at multiple levels:
1. SYNTAX: Basic Python compilation check
2. IMPORTS: Verify imports are valid PyNext modules
3. FULL: Syntax + imports + PyNext patterns

The validator helps the AI understand what went wrong so it can
reason about fixes rather than blindly retrying.

Example:
    validator = CodeValidator(level=ValidationLevel.FULL)
    result = validator.validate(code, "page")
    
    if not result.valid:
        print(f"Errors: {result.errors}")
        print(f"Suggestions: {result.suggestions}")
"""

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ============================================
# Validation Level
# ============================================

class ValidationLevel(str, Enum):
    """
    How thoroughly to validate generated code.
    
    - SYNTAX: Just compile() check - fast but minimal
    - IMPORTS: Syntax + verify imports are valid PyNext modules
    - FULL: Syntax + imports + PyNext patterns (signals, elements, decorators)
    """
    SYNTAX = "syntax"
    IMPORTS = "imports"
    FULL = "full"


# ============================================
# Validation Result
# ============================================

@dataclass
class ValidationResult:
    """
    Result of code validation.
    
    Attributes:
        valid: Whether the code is valid
        errors: List of error messages (blocking issues)
        warnings: List of warnings (non-blocking issues)
        suggestions: List of suggestions for improvement
        level: Validation level that was used
    
    Example:
        result = ValidationResult(
            valid=False,
            errors=["SyntaxError: invalid syntax at line 5"],
            warnings=["Missing docstring"],
            suggestions=["Consider using Signal for state management"]
        )
    """
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    level: ValidationLevel = ValidationLevel.SYNTAX
    
    def add_error(self, error: str) -> None:
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a suggestion for improvement."""
        self.suggestions.append(suggestion)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "level": self.level.value,
        }
    
    def format_for_ai(self) -> str:
        """Format results for AI consumption."""
        lines = []
        
        if self.errors:
            lines.append("## Errors (must fix)")
            for error in self.errors:
                lines.append(f"- {error}")
        
        if self.warnings:
            lines.append("\n## Warnings (should fix)")
            for warning in self.warnings:
                lines.append(f"- {warning}")
        
        if self.suggestions:
            lines.append("\n## Suggestions")
            for suggestion in self.suggestions:
                lines.append(f"- {suggestion}")
        
        return "\n".join(lines) if lines else "No issues found."


# ============================================
# PyNext Patterns
# ============================================

# Valid PyNext imports
PYNEXT_MODULES = {
    "pynext",
    "pynext.core",
    "pynext.islands",
    "pynext.actions",
    "pynext.api",
    "pynext.routing",
    "pynext.db",
    "pynext.db.table",
    "pynext.db.live",
    "pynext.server",
    "pynext.client",
}

# Valid elements from pynext
PYNEXT_ELEMENTS = {
    "div", "span", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "button", "form", "input_", "textarea", "select", "option",
    "ul", "ol", "li", "table", "tr", "td", "th", "thead", "tbody",
    "img", "video", "audio", "canvas", "svg",
    "header", "footer", "nav", "main", "section", "article", "aside",
    "label", "fieldset", "legend",
}

# Valid state primitives
PYNEXT_PRIMITIVES = {
    "Signal", "Computed", "Effect", "Memo", "Resource",
    "createSignal", "createEffect", "createMemo",
}

# Valid decorators
PYNEXT_DECORATORS = {
    "island", "action", "api", "middleware", "layout",
    "loading", "error", "template",
}

# Common mistakes
COMMON_MISTAKES = {
    "class=": "Use class_ instead of class for CSS classes",
    "input(": "Use input_() instead of input() for input elements",
    "for=": "Use for_ instead of for for label elements",
    ".value": "Signals are called like functions: count() not count.value",
    "useState": "PyNext uses Signal(), not React's useState",
    "useEffect": "PyNext uses Effect(), not React's useEffect",
    "className": "Use class_ for CSS classes in PyNext",
    "onClick": "Use on_click for event handlers in PyNext",
    "onChange": "Use on_change for event handlers in PyNext",
}


# ============================================
# Code Validator
# ============================================

class CodeValidator:
    """
    Validates AI-generated PyNext code.
    
    The validator checks code at multiple levels to help the AI
    understand exactly what went wrong.
    
    Attributes:
        level: Validation level (syntax, imports, full)
    
    Example:
        validator = CodeValidator(level=ValidationLevel.FULL)
        result = validator.validate(code, "page")
        
        if not result.valid:
            # Use errors for AI reasoning
            for error in result.errors:
                print(f"Error: {error}")
    """
    
    def __init__(self, level: ValidationLevel = ValidationLevel.FULL):
        """
        Initialize validator.
        
        Args:
            level: How thoroughly to validate
        """
        self.level = level
    
    def validate(
        self,
        code: str,
        generator_type: str = "component"
    ) -> ValidationResult:
        """
        Validate generated code.
        
        Args:
            code: The generated Python code
            generator_type: What type was generated (page, component, etc.)
        
        Returns:
            ValidationResult with errors, warnings, and suggestions
        """
        result = ValidationResult(level=self.level)
        
        # Level 1: Syntax check (always)
        self._check_syntax(code, result)
        if not result.valid:
            return result
        
        # Level 2: Import check
        if self.level in (ValidationLevel.IMPORTS, ValidationLevel.FULL):
            self._check_imports(code, result)
        
        # Level 3: Full PyNext pattern check
        if self.level == ValidationLevel.FULL:
            self._check_pynext_patterns(code, generator_type, result)
            self._check_common_mistakes(code, result)
        
        return result
    
    def _check_syntax(self, code: str, result: ValidationResult) -> None:
        """Check Python syntax validity."""
        try:
            compile(code, "<generated>", "exec")
        except SyntaxError as e:
            error_msg = f"SyntaxError: {e.msg}"
            if e.lineno:
                error_msg += f" at line {e.lineno}"
            if e.text:
                error_msg += f"\n  Code: {e.text.strip()}"
            result.add_error(error_msg)
    
    def _check_imports(self, code: str, result: ValidationResult) -> None:
        """Check import statements are valid."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return  # Already caught in syntax check
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._validate_import(alias.name, result)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._validate_import(node.module, result)
    
    def _validate_import(self, module: str, result: ValidationResult) -> None:
        """Validate a single import."""
        # Check if it's a pynext import
        if module.startswith("pynext"):
            # Get base module
            parts = module.split(".")
            base = ".".join(parts[:2]) if len(parts) > 1 else parts[0]
            
            if base not in PYNEXT_MODULES and module not in PYNEXT_MODULES:
                result.add_warning(
                    f"Unknown PyNext module: {module}. "
                    f"Valid modules: {', '.join(sorted(PYNEXT_MODULES))}"
                )
    
    def _check_pynext_patterns(
        self,
        code: str,
        generator_type: str,
        result: ValidationResult
    ) -> None:
        """Check PyNext-specific patterns."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return
        
        # Check for expected patterns based on generator type
        has_function = False
        has_decorator = False
        has_return = False
        uses_elements = False
        uses_signals = False
        
        for node in ast.walk(tree):
            # Check for function definitions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                has_function = True
                
                # Check for decorators
                for decorator in node.decorator_list:
                    has_decorator = True
                    if isinstance(decorator, ast.Name):
                        if decorator.id in PYNEXT_DECORATORS:
                            pass  # Valid decorator
                        elif decorator.id not in {"staticmethod", "classmethod", "property"}:
                            result.add_warning(
                                f"Unknown decorator @{decorator.id}. "
                                f"PyNext decorators: {', '.join(sorted(PYNEXT_DECORATORS))}"
                            )
            
            # Check for return statements
            if isinstance(node, ast.Return):
                has_return = True
            
            # Check for PyNext element calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in PYNEXT_ELEMENTS:
                        uses_elements = True
                    if node.func.id in PYNEXT_PRIMITIVES:
                        uses_signals = True
        
        # Generator-specific checks
        if generator_type in ("page", "component", "island", "layout"):
            if not has_function:
                result.add_error(
                    f"Missing function definition. "
                    f"A {generator_type} should define a function."
                )
            
            if not has_return:
                result.add_warning(
                    f"Missing return statement. "
                    f"A {generator_type} function should return PyNext elements."
                )
            
            if not uses_elements:
                result.add_suggestion(
                    "No PyNext elements found (div, button, etc.). "
                    "Consider using PyNext's HTML elements for the UI."
                )
        
        if generator_type == "island":
            if not has_decorator:
                result.add_error(
                    "Islands must have the @island decorator. "
                    "Add: from pynext.islands import island"
                )
            
            if not uses_signals:
                result.add_suggestion(
                    "Islands typically use Signals for state. "
                    "Consider using Signal() for reactive state."
                )
        
        if generator_type == "action":
            if not has_decorator:
                result.add_error(
                    "Server actions must have the @action decorator. "
                    "Add: from pynext.actions import action"
                )
        
        if generator_type == "api":
            if not has_decorator:
                result.add_error(
                    "API routes must have the @api decorator. "
                    "Add: from pynext.api import api"
                )
    
    def _check_common_mistakes(self, code: str, result: ValidationResult) -> None:
        """Check for common mistakes."""
        for mistake, suggestion in COMMON_MISTAKES.items():
            if mistake in code:
                result.add_warning(f"Possible mistake: '{mistake}' - {suggestion}")
        
        # Check for React patterns
        react_patterns = [
            ("useState", "Use Signal() instead of useState"),
            ("useEffect", "Use Effect() instead of useEffect"),
            ("useRef", "Use Signal() for refs in PyNext"),
            ("useCallback", "Functions don't need useCallback in PyNext"),
            ("useMemo", "Use Computed() instead of useMemo"),
            ("<div>", "Use div() function syntax, not JSX"),
            ("</div>", "Use div() function syntax, not JSX"),
            ("className=", "Use class_ instead of className"),
        ]
        
        for pattern, suggestion in react_patterns:
            if pattern in code:
                result.add_error(f"React pattern detected: {pattern}. {suggestion}")
        
        # Check for proper Signal usage
        if "Signal(" in code:
            # Check for .value access (wrong)
            if re.search(r'\w+\.value\b', code):
                result.add_error(
                    "Signals are accessed by calling them like functions. "
                    "Use count() not count.value"
                )
            
            # Check for direct assignment (wrong)
            if re.search(r'\w+\s*=\s*\w+\(\)\s*\+', code):
                # This might be legitimate, but flag it
                result.add_suggestion(
                    "To update a Signal, use signal.set(). "
                    "Example: count.set(count() + 1)"
                )


# ============================================
# Quick Validation Functions
# ============================================

def validate_syntax(code: str) -> ValidationResult:
    """Quick syntax-only validation."""
    return CodeValidator(ValidationLevel.SYNTAX).validate(code)


def validate_imports(code: str) -> ValidationResult:
    """Validate syntax and imports."""
    return CodeValidator(ValidationLevel.IMPORTS).validate(code)


def validate_full(code: str, generator_type: str = "component") -> ValidationResult:
    """Full validation including PyNext patterns."""
    return CodeValidator(ValidationLevel.FULL).validate(code, generator_type)


def is_valid_pynext_code(code: str) -> bool:
    """Quick check if code is valid PyNext."""
    result = validate_syntax(code)
    return result.valid

