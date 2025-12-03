"""
Interactive Session - Chat-like interface for app building.

Provides an interactive REPL for building and modifying
PyNext applications through conversation.

Example:
    session = AppSession(project_path=Path("."))
    await session.start()
    
    # Then in the session:
    # > Create a blog with user authentication
    # > Add dark mode toggle
    # > Show me the current files
"""

import asyncio
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .generator import AppGenerator, GenerationResult
from .planner import AppPlanner, AppPlan
from .context import ContextAnalyzer, ProjectContext
from .progress import SilentTracker

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """State of an interactive session."""
    project_path: Optional[Path] = None
    context: Optional[ProjectContext] = None
    current_plan: Optional[AppPlan] = None
    history: List[Dict[str, str]] = field(default_factory=list)
    mode: str = "plan"  # plan, agent, ask
    
    @property
    def has_project(self) -> bool:
        return self.project_path is not None


class AppSession:
    """
    Interactive session for building applications.
    
    Provides a chat-like interface where users can:
    - Create new applications
    - Add features to existing apps
    - View and modify plans
    - Get help and examples
    """
    
    COMMANDS = {
        "help": "Show available commands",
        "plan": "Show current plan",
        "execute": "Execute the current plan",
        "mode": "Change mode (plan/agent/ask)",
        "files": "List project files",
        "status": "Show session status",
        "quit": "Exit session",
        "clear": "Clear conversation history",
    }
    
    def __init__(
        self,
        project_path: Optional[Path] = None,
        config: Optional[Any] = None,
    ):
        """
        Initialize session.
        
        Args:
            project_path: Path to existing project (or None for new)
            config: AI configuration
        """
        self.config = config
        self.state = SessionState(project_path=project_path)
        self.generator = AppGenerator(config, tracker=SilentTracker())
        self.planner = AppPlanner(config)
        self.analyzer = ContextAnalyzer()
    
    async def start(self) -> None:
        """Start the interactive session."""
        self._print_welcome()
        
        # Analyze existing project if provided
        if self.state.project_path and self.state.project_path.exists():
            await self._analyze_project()
        
        # Main loop
        while True:
            try:
                user_input = self._get_input()
                
                if not user_input:
                    continue
                
                # Check for commands
                if user_input.startswith("/"):
                    command = user_input[1:].split()[0]
                    args = user_input[len(command) + 2:].strip()
                    should_continue = await self._handle_command(command, args)
                    if not should_continue:
                        break
                else:
                    # Handle natural language input
                    await self._handle_input(user_input)
                
            except KeyboardInterrupt:
                print("\n\nUse /quit to exit.")
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                print(f"\n❌ Error: {e}")
        
        print("\n👋 Goodbye!")
    
    def _print_welcome(self) -> None:
        """Print welcome message."""
        print("\n" + "=" * 50)
        print("🤖 PyNext App Builder")
        print("=" * 50)
        print("\nDescribe what you want to build, or type /help")
        
        if self.state.has_project:
            print(f"📁 Working with: {self.state.project_path}")
        else:
            print("📁 No project loaded (will create new)")
        
        print()
    
    def _get_input(self) -> str:
        """Get user input."""
        try:
            return input("\n> ").strip()
        except EOFError:
            return "/quit"
    
    async def _handle_command(self, command: str, args: str) -> bool:
        """
        Handle a command.
        
        Returns:
            True to continue, False to exit
        """
        command = command.lower()
        
        if command == "quit" or command == "exit":
            return False
        
        elif command == "help":
            self._show_help()
        
        elif command == "plan":
            self._show_plan()
        
        elif command == "execute":
            await self._execute_plan()
        
        elif command == "mode":
            self._change_mode(args)
        
        elif command == "files":
            self._show_files()
        
        elif command == "status":
            self._show_status()
        
        elif command == "clear":
            self.state.history.clear()
            print("✓ History cleared")
        
        elif command == "new":
            await self._create_new_project(args)
        
        elif command == "add":
            await self._add_feature(args)
        
        else:
            print(f"Unknown command: {command}")
            print("Type /help for available commands")
        
        return True
    
    async def _handle_input(self, user_input: str) -> None:
        """Handle natural language input."""
        # Add to history
        self.state.history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Determine intent
        input_lower = user_input.lower()
        
        if any(w in input_lower for w in ["create", "build", "make", "new"]):
            # Creating something
            if self.state.has_project:
                await self._add_feature(user_input)
            else:
                await self._create_new_project(user_input)
        
        elif any(w in input_lower for w in ["add", "include", "implement"]):
            # Adding to existing
            await self._add_feature(user_input)
        
        elif any(w in input_lower for w in ["show", "list", "what"]):
            # Information request
            if "file" in input_lower:
                self._show_files()
            elif "plan" in input_lower:
                self._show_plan()
            else:
                self._show_status()
        
        else:
            # Default: treat as app/feature description
            if self.state.has_project:
                await self._add_feature(user_input)
            else:
                await self._create_new_project(user_input)
    
    async def _create_new_project(self, description: str) -> None:
        """Create a new project from description."""
        print("\n🔍 Analyzing requirements...")
        
        # Create plan
        plan = await self.planner.create_plan(description)
        self.state.current_plan = plan
        
        # Show plan
        print("\n" + plan.to_markdown())
        
        # Ask for confirmation in plan mode
        if self.state.mode == "plan":
            response = input("\nProceed with this plan? [Y/n] ").strip().lower()
            if response not in ("", "y", "yes"):
                print("Plan saved. Use /execute when ready.")
                return
        
        await self._execute_plan()
    
    async def _add_feature(self, feature: str) -> None:
        """Add a feature to existing project."""
        if not self.state.has_project:
            # Ask for project path
            path = input("Enter project path: ").strip()
            if not path:
                print("No project path provided")
                return
            self.state.project_path = Path(path).resolve()
            await self._analyze_project()
        
        print("\n🔍 Planning feature...")
        
        # Create plan
        plan = await self.planner.plan_feature(
            feature=feature,
            project_path=self.state.project_path,
        )
        self.state.current_plan = plan
        
        if not plan.operations:
            print("⚠️  Could not determine what to create")
            return
        
        # Show plan
        print("\n" + plan.to_markdown())
        
        # Ask for confirmation in plan mode
        if self.state.mode == "plan":
            response = input("\nProceed? [Y/n] ").strip().lower()
            if response not in ("", "y", "yes"):
                print("Plan saved. Use /execute when ready.")
                return
        
        await self._execute_plan()
    
    async def _execute_plan(self) -> None:
        """Execute the current plan."""
        if not self.state.current_plan:
            print("No plan to execute. Describe what you want to build first.")
            return
        
        plan = self.state.current_plan
        
        # Determine output directory
        if self.state.has_project:
            output_dir = self.state.project_path
        else:
            output_dir = Path(f"./{plan.name}").resolve()
            self.state.project_path = output_dir
        
        print(f"\n🚀 Generating to {output_dir}...")
        
        # Execute
        result = await self.generator.new_app(
            description=plan.description,
            output_dir=output_dir,
            mode="agent",  # Use agent mode for execution
            complexity=plan.complexity,
        )
        
        if result.success:
            print(f"\n✅ Generated {len(result.generated_files)} files!")
            await self._analyze_project()  # Refresh context
        else:
            print(f"\n⚠️  Generation completed with issues")
            if result.failed_files:
                print(f"   Failed: {', '.join(result.failed_files)}")
        
        self.state.current_plan = None
    
    async def _analyze_project(self) -> None:
        """Analyze the current project."""
        if not self.state.project_path:
            return
        
        try:
            self.state.context = await self.analyzer.analyze(self.state.project_path)
            print(f"📊 Analyzed project: {self.state.context.get_summary()}")
        except Exception as e:
            print(f"⚠️  Could not analyze project: {e}")
    
    def _show_help(self) -> None:
        """Show help message."""
        print("\n📚 Commands:")
        for cmd, desc in self.COMMANDS.items():
            print(f"  /{cmd:12} - {desc}")
        
        print("\n💡 Examples:")
        print("  > Create a blog with user authentication")
        print("  > Add a dark mode toggle")
        print("  > /mode agent")
        print("  > /plan")
    
    def _show_plan(self) -> None:
        """Show current plan."""
        if self.state.current_plan:
            print("\n" + self.state.current_plan.to_markdown())
        else:
            print("No current plan.")
    
    def _change_mode(self, mode: str) -> None:
        """Change generation mode."""
        mode = mode.lower().strip()
        if mode in ("plan", "agent", "ask"):
            self.state.mode = mode
            print(f"✓ Mode changed to: {mode}")
        else:
            print(f"Unknown mode: {mode}")
            print("Available: plan, agent, ask")
    
    def _show_files(self) -> None:
        """Show project files."""
        if not self.state.context:
            if self.state.has_project:
                print("Run /status first to analyze project")
            else:
                print("No project loaded")
            return
        
        ctx = self.state.context
        
        print("\n📁 Project Files:")
        if ctx.pages:
            print(f"\n  Pages ({len(ctx.pages)}):")
            for p in ctx.pages[:10]:
                print(f"    - {p}")
        
        if ctx.components:
            print(f"\n  Components ({len(ctx.components)}):")
            for c in ctx.components[:10]:
                print(f"    - {c}")
        
        if ctx.models:
            print(f"\n  Models ({len(ctx.models)}):")
            for m in ctx.models[:10]:
                print(f"    - {m}")
    
    def _show_status(self) -> None:
        """Show session status."""
        print("\n📊 Session Status:")
        print(f"  Project: {self.state.project_path or 'None'}")
        print(f"  Mode: {self.state.mode}")
        print(f"  Has Plan: {'Yes' if self.state.current_plan else 'No'}")
        print(f"  History: {len(self.state.history)} messages")
        
        if self.state.context:
            print(f"\n  {self.state.context.get_summary()}")


async def run_session(project_path: Optional[str] = None) -> None:
    """
    Run an interactive session.
    
    Args:
        project_path: Optional path to existing project
    """
    path = Path(project_path) if project_path else None
    session = AppSession(project_path=path)
    await session.start()

