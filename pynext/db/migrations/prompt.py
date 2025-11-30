"""
Interactive Prompts for Migrations.

Handles user interaction for ambiguous changes like renames.

Design: Clear, concise prompts with sensible defaults.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pynext.db.migrations.changes import Change
    from pynext.db.migrations.detector import AmbiguousChange


@dataclass
class PromptResult:
    """Result of resolving ambiguous changes."""
    resolved_changes: List["Change"]
    skipped: int


class InteractivePrompt:
    """
    Handles interactive prompts for migration generation.
    
    Prompts the user to resolve ambiguous changes like:
    - Column/table renames (vs add + drop)
    - Type narrowing (may lose data)
    - Dropping tables/columns with data
    
    Usage:
        prompt = InteractivePrompt()
        
        for ambig in result.ambiguous:
            change = prompt.ask(ambig)
            if change:
                changes.append(change)
    """
    
    def __init__(
        self,
        interactive: bool = True,
        use_defaults: bool = False,
        output: Optional["TextIO"] = None,
        input_fn: Optional[callable] = None,
    ):
        """
        Args:
            interactive: Whether to prompt for user input
            use_defaults: If True, use default answers without prompting
            output: Output stream (default: sys.stdout)
            input_fn: Function for getting input (default: input())
        """
        self.interactive = interactive
        self.use_defaults = use_defaults
        self.output = output or sys.stdout
        self.input_fn = input_fn or input
    
    def ask(self, ambig: "AmbiguousChange") -> List["Change"]:
        """
        Ask user about an ambiguous change.
        
        Args:
            ambig: The ambiguous change to resolve
            
        Returns:
            List of changes based on user response
        """
        if self.use_defaults:
            return self._apply_default(ambig)
        
        if not self.interactive:
            # Non-interactive: use default
            return self._apply_default(ambig)
        
        self._print(f"\n{ambig.description}")
        
        default_char = "Y" if ambig.default else "N"
        prompt = f"{ambig.question} [y/N]: " if not ambig.default else f"{ambig.question} [Y/n]: "
        
        try:
            response = self.input_fn(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            self._print("\nAborted.")
            return self._apply_default(ambig)
        
        if response in ("y", "yes"):
            return [ambig.if_yes]
        elif response in ("n", "no"):
            return ambig.if_no
        else:
            # Empty = use default
            return self._apply_default(ambig)
    
    def resolve_all(self, ambiguous: List["AmbiguousChange"]) -> PromptResult:
        """
        Resolve all ambiguous changes.
        
        Args:
            ambiguous: List of ambiguous changes
            
        Returns:
            PromptResult with resolved changes
        """
        resolved = []
        skipped = 0
        
        for ambig in ambiguous:
            changes = self.ask(ambig)
            if changes:
                resolved.extend(changes)
            else:
                skipped += 1
        
        return PromptResult(resolved_changes=resolved, skipped=skipped)
    
    def confirm_destructive(self, changes: List["Change"]) -> bool:
        """
        Confirm destructive changes before proceeding.
        
        Args:
            changes: List of changes to check
            
        Returns:
            True if user confirms, False otherwise
        """
        destructive = [c for c in changes if c.is_destructive()]
        
        if not destructive:
            return True
        
        self._print("\n⚠️  The following changes may cause data loss:\n")
        for change in destructive:
            self._print(f"  - {change.description()}")
        
        if self.use_defaults:
            self._print("\nSkipping confirmation (using defaults)")
            return False
        
        if not self.interactive:
            self._print("\nRun with --force to apply destructive changes")
            return False
        
        try:
            response = self.input_fn("\nContinue? [y/N]: ").strip().lower()
            return response in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False
    
    def confirm_empty_migration(self) -> bool:
        """Ask if user wants to create an empty migration."""
        if not self.interactive or self.use_defaults:
            return False
        
        self._print("\nNo changes detected.")
        
        try:
            response = self.input_fn("Create an empty migration? [y/N]: ").strip().lower()
            return response in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False
    
    def _apply_default(self, ambig: "AmbiguousChange") -> List["Change"]:
        """Apply the default answer to an ambiguous change."""
        if ambig.default:
            return [ambig.if_yes]
        else:
            return ambig.if_no
    
    def _print(self, message: str) -> None:
        """Print a message."""
        print(message, file=self.output)


class NonInteractivePrompt(InteractivePrompt):
    """
    Non-interactive prompt that uses defaults.
    
    For CI/CD or scripted use.
    """
    
    def __init__(self, output: Optional["TextIO"] = None):
        super().__init__(
            interactive=False,
            use_defaults=True,
            output=output,
        )


class TestPrompt(InteractivePrompt):
    """
    Test prompt with predefined answers.
    
    For unit testing.
    """
    
    def __init__(self, answers: List[str], output: Optional["TextIO"] = None):
        """
        Args:
            answers: List of answers to return in order
            output: Output stream
        """
        self._answers = list(reversed(answers))  # Pop from end
        self._output_capture: List[str] = []
        
        super().__init__(
            interactive=True,
            use_defaults=False,
            output=output,
            input_fn=self._mock_input,
        )
    
    def _mock_input(self, prompt: str) -> str:
        """Return the next predefined answer."""
        self._print(prompt)
        if self._answers:
            return self._answers.pop()
        return ""
    
    @property
    def captured_output(self) -> List[str]:
        """Get all captured output."""
        return self._output_capture


__all__ = [
    "InteractivePrompt",
    "NonInteractivePrompt",
    "TestPrompt",
    "PromptResult",
]

