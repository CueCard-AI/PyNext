"""
PyNext Linting - Base Classes

Foundation for all PyNext linting rules.
Provides consistent error reporting and AST traversal.
"""

from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, Set


@dataclass
class LintError:
    """
    A linting error with fix suggestion.
    
    Contains all information needed to display the error
    and optionally fix it.
    """
    rule: str           # Rule ID (e.g., "PNX001")
    message: str        # Human-readable description
    line: int           # Line number (1-indexed)
    column: int         # Column number (0-indexed)
    severity: str       # "error", "warning", "info"
    
    # Optional fix information
    fix: Optional[str] = None           # Suggested fix code
    fix_description: Optional[str] = None  # What the fix does
    
    # Optional context
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    def __str__(self) -> str:
        severity_icon = {
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
        }.get(self.severity, "•")
        
        return f"{severity_icon} {self.rule}: {self.message} (line {self.line})"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON output."""
        return {
            "rule": self.rule,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
            "fix": self.fix,
            "fix_description": self.fix_description,
        }


@dataclass
class LintResult:
    """
    Result of linting a file or project.
    """
    errors: List[LintError]
    files_checked: int = 1
    
    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "error")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "warning")
    
    @property
    def info_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "info")
    
    @property
    def has_errors(self) -> bool:
        return self.error_count > 0
    
    def summary(self) -> str:
        """Get a summary of lint results."""
        parts = []
        if self.error_count:
            parts.append(f"{self.error_count} error(s)")
        if self.warning_count:
            parts.append(f"{self.warning_count} warning(s)")
        if self.info_count:
            parts.append(f"{self.info_count} info(s)")
        
        if not parts:
            return "✅ No issues found"
        
        return f"Found: {', '.join(parts)}"


class BaseLinter(ABC):
    """
    Base class for all PyNext linters.
    
    Provides common functionality for AST traversal
    and error collection.
    """
    
    def __init__(self):
        self.errors: List[LintError] = []
        self.filename: str = "<unknown>"
        self.source: str = ""
        self.enabled_rules: Set[str] = set()
    
    @abstractmethod
    def check(
        self,
        source: str,
        filename: str,
        enabled_rules: Set[str],
    ) -> List[LintError]:
        """
        Check source code for issues.
        
        Args:
            source: Python source code
            filename: Name of the file
            enabled_rules: Set of enabled rule IDs
            
        Returns:
            List of LintError objects
        """
        pass
    
    def add_error(
        self,
        rule: str,
        message: str,
        line: int,
        column: int = 0,
        severity: str = "error",
        fix: Optional[str] = None,
        fix_description: Optional[str] = None,
    ) -> None:
        """Add an error to the results."""
        if rule in self.enabled_rules:
            self.errors.append(LintError(
                rule=rule,
                message=message,
                line=line,
                column=column,
                severity=severity,
                fix=fix,
                fix_description=fix_description,
            ))
    
    def parse_source(self, source: str) -> Optional[ast.AST]:
        """Parse source code into AST."""
        try:
            return ast.parse(source)
        except SyntaxError as e:
            self.errors.append(LintError(
                rule="PNX000",
                message=f"Syntax error: {e.msg}",
                line=e.lineno or 0,
                column=e.offset or 0,
                severity="error",
            ))
            return None
    
    @staticmethod
    def explain(rule_id: str) -> str:
        """Get detailed explanation for a rule."""
        return f"No detailed explanation available for {rule_id}"

