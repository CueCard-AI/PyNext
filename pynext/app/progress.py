"""
Progress Tracker - Track and display generation progress.

Provides visual feedback during app generation with
progress bars, status updates, and summaries.

Example:
    tracker = ProgressTracker()
    
    tracker.start_plan(plan)
    
    for op in plan.operations:
        tracker.start_operation(op)
        # ... generate file ...
        tracker.complete_operation(op, success=True)
    
    tracker.show_summary(result)
"""

import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class OperationStatus(str, Enum):
    """Status of an operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class OperationProgress:
    """Progress for a single operation."""
    path: str
    status: OperationStatus = OperationStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Get operation duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


@dataclass
class GenerationProgress:
    """Overall generation progress."""
    total: int = 0
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    operations: List[OperationProgress] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def success_count(self) -> int:
        return sum(1 for op in self.operations if op.status == OperationStatus.SUCCESS)
    
    @property
    def progress_percent(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.completed + self.failed + self.skipped) / self.total * 100
    
    @property
    def total_duration(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0.0


class ProgressTracker:
    """
    Track and display generation progress.
    
    Provides console output with progress indicators,
    operation status, and summaries.
    """
    
    # Status icons
    ICONS = {
        OperationStatus.PENDING: "⏳",
        OperationStatus.IN_PROGRESS: "🔄",
        OperationStatus.SUCCESS: "✓",
        OperationStatus.FAILED: "✗",
        OperationStatus.SKIPPED: "○",
    }
    
    def __init__(self, verbose: bool = True, use_colors: bool = True):
        """
        Initialize tracker.
        
        Args:
            verbose: Show detailed output
            use_colors: Use ANSI colors
        """
        self.verbose = verbose
        self.use_colors = use_colors
        self.progress = GenerationProgress()
        self._current_operation: Optional[OperationProgress] = None
    
    def start_plan(self, plan: Any) -> None:
        """
        Start tracking a plan.
        
        Args:
            plan: AppPlan to track
        """
        self.progress = GenerationProgress(
            total=len(plan.operations),
            started_at=datetime.utcnow(),
        )
        
        # Initialize operation progress
        for op in plan.operations:
            self.progress.operations.append(OperationProgress(path=op.path))
        
        if self.verbose:
            self._print(f"\n🚀 Starting generation of {plan.name}")
            self._print(f"   {self.progress.total} files to create\n")
    
    def start_operation(self, operation: Any) -> None:
        """
        Mark an operation as starting.
        
        Args:
            operation: FileOperation starting
        """
        # Find operation progress
        for op_progress in self.progress.operations:
            if op_progress.path == operation.path:
                op_progress.status = OperationStatus.IN_PROGRESS
                op_progress.started_at = datetime.utcnow()
                self._current_operation = op_progress
                break
        
        if self.verbose:
            idx = self.progress.completed + self.progress.failed + self.progress.skipped + 1
            self._print(
                f"  [{idx}/{self.progress.total}] Creating {operation.path}...",
                end=" ",
                flush=True,
            )
    
    def complete_operation(
        self,
        operation: Any,
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        Mark an operation as complete.
        
        Args:
            operation: FileOperation completed
            success: Whether it succeeded
            error: Error message if failed
        """
        # Find operation progress
        for op_progress in self.progress.operations:
            if op_progress.path == operation.path:
                op_progress.completed_at = datetime.utcnow()
                
                if success:
                    op_progress.status = OperationStatus.SUCCESS
                    self.progress.completed += 1
                else:
                    op_progress.status = OperationStatus.FAILED
                    op_progress.error = error
                    self.progress.failed += 1
                break
        
        if self.verbose:
            if success:
                self._print(self._color("✓", "green"))
            else:
                self._print(self._color("✗", "red"))
                if error:
                    self._print(f"      Error: {error}")
    
    def skip_operation(self, operation: Any, reason: str = "") -> None:
        """
        Mark an operation as skipped.
        
        Args:
            operation: FileOperation skipped
            reason: Reason for skipping
        """
        for op_progress in self.progress.operations:
            if op_progress.path == operation.path:
                op_progress.status = OperationStatus.SKIPPED
                op_progress.error = reason
                self.progress.skipped += 1
                break
        
        if self.verbose:
            self._print(f"  [○] Skipped {operation.path}")
            if reason:
                self._print(f"      Reason: {reason}")
    
    def show_summary(self, result: Optional[Any] = None) -> None:
        """
        Show generation summary.
        
        Args:
            result: GenerationResult (optional)
        """
        self.progress.completed_at = datetime.utcnow()
        
        self._print("\n" + "─" * 50)
        
        if self.progress.failed == 0:
            self._print(self._color("✅ Generation complete!", "green"))
        else:
            self._print(self._color("⚠️  Generation completed with errors", "yellow"))
        
        self._print(f"\n  Files created: {self.progress.success_count}")
        
        if self.progress.failed > 0:
            self._print(f"  Files failed:  {self.progress.failed}")
        
        if self.progress.skipped > 0:
            self._print(f"  Files skipped: {self.progress.skipped}")
        
        self._print(f"  Total time:    {self.progress.total_duration:.1f}s")
        
        # Show failed operations
        failed_ops = [op for op in self.progress.operations if op.status == OperationStatus.FAILED]
        if failed_ops:
            self._print(f"\n  {self._color('Failed files:', 'red')}")
            for op in failed_ops:
                self._print(f"    - {op.path}: {op.error or 'Unknown error'}")
        
        self._print("")
    
    def show_progress_bar(self) -> None:
        """Show a progress bar."""
        percent = self.progress.progress_percent
        filled = int(percent / 5)
        empty = 20 - filled
        
        bar = "█" * filled + "░" * empty
        self._print(f"\r  [{bar}] {percent:.0f}%", end="", flush=True)
    
    def _print(self, message: str, **kwargs) -> None:
        """Print a message."""
        print(message, **kwargs)
    
    def _color(self, text: str, color: str) -> str:
        """Apply ANSI color to text."""
        if not self.use_colors:
            return text
        
        colors = {
            "green": "\033[92m",
            "red": "\033[91m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "reset": "\033[0m",
        }
        
        return f"{colors.get(color, '')}{text}{colors['reset']}"


class SilentTracker(ProgressTracker):
    """Silent tracker that doesn't print anything."""
    
    def __init__(self):
        super().__init__(verbose=False)
    
    def _print(self, message: str, **kwargs) -> None:
        pass

