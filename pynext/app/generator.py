"""
App Generator - Main entry point for application generation.

Supports three modes:
- Plan: Show plan, wait for approval, generate
- Agent: Autonomous generation with minimal prompts
- Ask: Interactive mode with approval at each step

Example:
    generator = AppGenerator(config)
    
    # Create new app
    result = await generator.new_app(
        "task manager with auth",
        output_dir=Path("./my-app"),
        mode="plan",
    )
    
    # Add feature to existing app
    result = await generator.add_feature(
        "dark mode toggle",
        project_path=Path("./my-app"),
        mode="ask",
    )
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Literal, Optional
import logging

from .planner import AppPlanner, AppPlan, FileOperation, OperationType
from .context import ContextAnalyzer, ProjectContext
from .file_generator import FileGenerator, BatchFileGenerator, GeneratedFile
from .progress import ProgressTracker, SilentTracker
from .rollback import RollbackManager

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of app generation."""
    success: bool
    plan: AppPlan
    generated_files: Dict[str, GeneratedFile] = field(default_factory=dict)
    failed_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    output_dir: Optional[Path] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    @property
    def duration(self) -> float:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "plan": self.plan.to_dict(),
            "generated_files": list(self.generated_files.keys()),
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "duration": self.duration,
            "error": self.error,
        }


class AppGenerator:
    """
    Main application generator.
    
    Orchestrates planning, file generation, and progress
    tracking for creating complete applications.
    """
    
    def __init__(
        self,
        config: Optional[Any] = None,
        tracker: Optional[ProgressTracker] = None,
    ):
        """
        Initialize app generator.
        
        Args:
            config: AIConfig for AI calls
            tracker: Progress tracker (created if None)
        """
        self.config = config
        self.planner = AppPlanner(config)
        self.file_generator = FileGenerator(config)
        self.tracker = tracker or ProgressTracker()
    
    async def new_app(
        self,
        description: str,
        output_dir: Path,
        mode: Literal["plan", "agent", "ask"] = "plan",
        complexity: str = "auto",
        confirm_callback: Optional[Callable[[AppPlan], bool]] = None,
        file_callback: Optional[Callable[[FileOperation, str], bool]] = None,
    ) -> GenerationResult:
        """
        Create a new application.
        
        Args:
            description: Natural language description
            output_dir: Directory to create app in
            mode: Generation mode (plan, agent, ask)
            complexity: App complexity level
            confirm_callback: Callback for plan confirmation (plan mode)
            file_callback: Callback for file confirmation (ask mode)
        
        Returns:
            GenerationResult with generated files
        """
        output_dir = Path(output_dir).resolve()
        
        # Create plan
        plan = await self.planner.create_plan(
            description=description,
            complexity=complexity,
        )
        
        # Handle based on mode
        if mode == "plan":
            return await self._execute_plan_mode(
                plan=plan,
                output_dir=output_dir,
                confirm_callback=confirm_callback,
            )
        elif mode == "agent":
            return await self._execute_agent_mode(
                plan=plan,
                output_dir=output_dir,
            )
        elif mode == "ask":
            return await self._execute_ask_mode(
                plan=plan,
                output_dir=output_dir,
                file_callback=file_callback,
            )
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    async def add_feature(
        self,
        feature: str,
        project_path: Path,
        mode: Literal["plan", "agent", "ask"] = "plan",
        confirm_callback: Optional[Callable[[AppPlan], bool]] = None,
        file_callback: Optional[Callable[[FileOperation, str], bool]] = None,
    ) -> GenerationResult:
        """
        Add a feature to an existing project.
        
        Args:
            feature: Feature description
            project_path: Path to existing project
            mode: Generation mode
            confirm_callback: Plan confirmation callback
            file_callback: File confirmation callback
        
        Returns:
            GenerationResult with changes
        """
        project_path = Path(project_path).resolve()
        
        # Analyze existing project
        analyzer = ContextAnalyzer()
        context = await analyzer.analyze(project_path)
        
        # Create plan for feature
        plan = await self.planner.plan_feature(
            feature=feature,
            project_path=project_path,
        )
        
        if not plan.operations:
            return GenerationResult(
                success=False,
                plan=plan,
                error="Could not plan feature additions",
            )
        
        # Execute based on mode
        if mode == "plan":
            return await self._execute_plan_mode(
                plan=plan,
                output_dir=project_path,
                confirm_callback=confirm_callback,
                context=context,
            )
        elif mode == "agent":
            return await self._execute_agent_mode(
                plan=plan,
                output_dir=project_path,
                context=context,
            )
        else:
            return await self._execute_ask_mode(
                plan=plan,
                output_dir=project_path,
                file_callback=file_callback,
                context=context,
            )
    
    async def _execute_plan_mode(
        self,
        plan: AppPlan,
        output_dir: Path,
        confirm_callback: Optional[Callable[[AppPlan], bool]] = None,
        context: Optional[ProjectContext] = None,
    ) -> GenerationResult:
        """
        Execute in plan mode - show plan, get approval, generate.
        """
        # Show plan
        print("\n" + plan.to_markdown())
        print()
        
        # Get confirmation
        if confirm_callback:
            approved = confirm_callback(plan)
        else:
            # Default: ask user
            response = input("Proceed? [Y/n/edit] ").strip().lower()
            approved = response in ("", "y", "yes")
        
        if not approved:
            return GenerationResult(
                success=False,
                plan=plan,
                output_dir=output_dir,
                error="Plan not approved",
            )
        
        # Generate all files
        return await self._generate_files(
            plan=plan,
            output_dir=output_dir,
            context=context,
        )
    
    async def _execute_agent_mode(
        self,
        plan: AppPlan,
        output_dir: Path,
        context: Optional[ProjectContext] = None,
    ) -> GenerationResult:
        """
        Execute in agent mode - generate autonomously.
        """
        # Just generate all files
        return await self._generate_files(
            plan=plan,
            output_dir=output_dir,
            context=context,
        )
    
    async def _execute_ask_mode(
        self,
        plan: AppPlan,
        output_dir: Path,
        file_callback: Optional[Callable[[FileOperation, str], bool]] = None,
        context: Optional[ProjectContext] = None,
    ) -> GenerationResult:
        """
        Execute in ask mode - confirm each file.
        """
        result = GenerationResult(
            success=True,
            plan=plan,
            output_dir=output_dir,
        )
        
        # Create rollback manager
        rollback = RollbackManager(output_dir)
        rollback.checkpoint("Before generation")
        
        self.tracker.start_plan(plan)
        
        ordered_ops = plan.get_ordered_operations()
        previous_files: Dict[str, str] = {}
        
        for operation in ordered_ops:
            # Generate preview
            generated = await self.file_generator.generate_file(
                operation=operation,
                context=context,
                previous_files=previous_files,
            )
            
            # Show preview and ask
            print(f"\n[{len(result.generated_files) + 1}/{len(ordered_ops)}] {operation.action.value.title()} {operation.path}?")
            print(f"\nPreview:")
            print("```python")
            # Show first 30 lines
            preview_lines = generated.content.split("\n")[:30]
            print("\n".join(preview_lines))
            if len(generated.content.split("\n")) > 30:
                print("... (truncated)")
            print("```")
            
            if file_callback:
                approved = file_callback(operation, generated.content)
            else:
                response = input("\nCreate this file? [Y/n/edit] ").strip().lower()
                approved = response in ("", "y", "yes")
            
            if approved:
                # Write file
                file_path = output_dir / operation.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(generated.content, encoding="utf-8")
                
                result.generated_files[operation.path] = generated
                previous_files[operation.path] = generated.content
                self.tracker.complete_operation(operation, success=True)
            else:
                result.skipped_files.append(operation.path)
                self.tracker.skip_operation(operation, "User declined")
        
        rollback.commit()
        result.completed_at = datetime.utcnow()
        
        self.tracker.show_summary(result)
        
        return result
    
    async def _generate_files(
        self,
        plan: AppPlan,
        output_dir: Path,
        context: Optional[ProjectContext] = None,
    ) -> GenerationResult:
        """
        Generate all files in a plan.
        """
        result = GenerationResult(
            success=True,
            plan=plan,
            output_dir=output_dir,
        )
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create rollback manager
        rollback = RollbackManager(output_dir)
        rollback.checkpoint("Before generation")
        
        self.tracker.start_plan(plan)
        
        # Get ordered operations
        ordered_ops = plan.get_ordered_operations()
        previous_files: Dict[str, str] = {}
        
        for operation in ordered_ops:
            self.tracker.start_operation(operation)
            
            try:
                # Generate file
                generated = await self.file_generator.generate_file(
                    operation=operation,
                    context=context,
                    previous_files=previous_files,
                )
                
                # Write file
                file_path = output_dir / operation.path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(generated.content, encoding="utf-8")
                
                result.generated_files[operation.path] = generated
                previous_files[operation.path] = generated.content
                
                self.tracker.complete_operation(operation, success=True)
                
            except Exception as e:
                logger.error(f"Failed to generate {operation.path}: {e}")
                result.failed_files.append(operation.path)
                result.success = False
                self.tracker.complete_operation(operation, success=False, error=str(e))
        
        # Commit or rollback
        if result.success:
            rollback.commit()
        
        result.completed_at = datetime.utcnow()
        
        self.tracker.show_summary(result)
        
        return result


# Convenience functions

async def create_app(
    description: str,
    output_dir: str = ".",
    mode: str = "plan",
    complexity: str = "auto",
) -> GenerationResult:
    """
    Create a new PyNext application.
    
    Args:
        description: Natural language description
        output_dir: Output directory
        mode: plan, agent, or ask
        complexity: minimal, small, medium, large, enterprise, or auto
    
    Returns:
        GenerationResult
    """
    generator = AppGenerator()
    return await generator.new_app(
        description=description,
        output_dir=Path(output_dir),
        mode=mode,
        complexity=complexity,
    )


async def add_feature(
    feature: str,
    project_path: str = ".",
    mode: str = "plan",
) -> GenerationResult:
    """
    Add a feature to an existing project.
    
    Args:
        feature: Feature description
        project_path: Path to project
        mode: plan, agent, or ask
    
    Returns:
        GenerationResult
    """
    generator = AppGenerator()
    return await generator.add_feature(
        feature=feature,
        project_path=Path(project_path),
        mode=mode,
    )

