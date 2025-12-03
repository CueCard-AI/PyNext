"""
Interactive Session - Chat-like interface for app building.

Provides an interactive REPL for building and modifying
PyNext applications through conversation.

Features:
- Persistent memory across sessions
- Configurable via pynext.toml
- Automatic summarization of long conversations
- Checkpoints for rollback

Example:
    session = AppSession(project_path=Path("."))
    await session.start()
    
    # Then in the session:
    # > Create a blog with user authentication
    # > Add dark mode toggle
    # > Show me the current files
    # > /memory show
    # > /config show
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
from .memory import SessionMemory, SyncConfig, get_memory, reset_memory
from .config import PyNextConfig, ConfigResolver, ConfigContext, get_config, reset_config

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
    - Manage memory and config
    """
    
    COMMANDS = {
        "help": "Show available commands",
        "plan": "Show current plan",
        "execute": "Execute the current plan",
        "mode": "Change mode (plan/agent/ask)",
        "files": "List project files",
        "status": "Show session status",
        "memory": "Memory commands (show, clear, flush, stats)",
        "config": "Config commands (show, reload)",
        "checkpoint": "Create a checkpoint",
        "quit": "Exit session",
        "clear": "Clear conversation history",
    }
    
    def __init__(
        self,
        project_path: Optional[Path] = None,
        config: Optional[PyNextConfig] = None,
    ):
        """
        Initialize session.
        
        Args:
            project_path: Path to existing project (or None for new)
            config: PyNext configuration (loaded from file if not provided)
        """
        self.project_path = project_path or Path.cwd()
        
        # Load config
        self.config = config or PyNextConfig.load(self.project_path)
        
        # Initialize memory with config settings
        sync_config = SyncConfig(
            mode=self.config.memory.sync_mode,
            triggers=self.config.memory.sync_on,
            batch_size=self.config.memory.sync_batch_size,
            interval=self.config.memory.sync_interval,
            sync_entries=self.config.memory.sync_entries,
            sync_summaries=self.config.memory.sync_summaries,
            sync_checkpoints=self.config.memory.sync_checkpoints,
            sync_preferences=self.config.memory.sync_preferences,
            exclude_roles=self.config.memory.exclude_roles,
            min_content_length=self.config.memory.min_content_length,
            max_entries_in_memory=self.config.memory.max_entries_in_memory,
        )
        self.memory = SessionMemory(
            project_path=self.project_path,
            sync_config=sync_config,
        )
        
        # Session state
        self.state = SessionState(
            project_path=project_path,
            mode=self.config.ai.mode,
        )
        
        # Initialize components
        self.generator = AppGenerator(config, tracker=SilentTracker())
        self.planner = AppPlanner(config)
        self.analyzer = ContextAnalyzer()
        self.resolver = ConfigResolver(self.config)
    
    async def start(self) -> None:
        """Start the interactive session."""
        # Load memory from previous session
        self.memory.load()
        
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
                    parts = user_input[1:].split(maxsplit=1)
                    command = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""
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
        
        # Save memory on exit
        self.memory.flush(force=True)
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
        
        # Show memory stats if we have history
        stats = self.memory.stats()
        if stats["entries"] > 0:
            print(f"💾 Loaded {stats['entries']} entries from previous session")
        
        print(f"⚙️  Mode: {self.state.mode}")
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
        
        elif command == "memory":
            await self._handle_memory_command(args)
        
        elif command == "config":
            self._handle_config_command(args)
        
        elif command == "checkpoint":
            await self._create_checkpoint(args)
        
        else:
            print(f"Unknown command: {command}")
            print("Type /help for available commands")
        
        return True
    
    async def _handle_memory_command(self, args: str) -> None:
        """Handle memory subcommands."""
        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower() if parts else "show"
        subargs = parts[1] if len(parts) > 1 else ""
        
        if subcommand == "show":
            self._show_memory(subargs)
        elif subcommand == "clear":
            confirm = input("Clear all memory? This cannot be undone. [y/N] ").strip().lower()
            if confirm == "y":
                self.memory.clear()
                print("✓ Memory cleared")
            else:
                print("Cancelled")
        elif subcommand == "flush":
            count = self.memory.flush(force=True)
            print(f"✓ Flushed {count} records to disk")
        elif subcommand == "stats":
            self._show_memory_stats()
        elif subcommand == "export":
            format_type = subargs or "markdown"
            output = self.memory.export(format_type)
            print(output)
        elif subcommand == "compact":
            self.memory.compact()
            print("✓ Memory compacted")
        elif subcommand == "sync":
            self._handle_sync_command(subargs)
        else:
            print(f"Unknown memory command: {subcommand}")
            print("Available: show, clear, flush, stats, export, compact, sync")
    
    def _handle_sync_command(self, args: str) -> None:
        """Handle memory sync subcommands."""
        if args == "--pause":
            self.memory.pause_sync()
            print("✓ Sync paused")
        elif args == "--resume":
            self.memory.resume_sync()
            print("✓ Sync resumed")
        elif args == "--status":
            paused = "paused" if self.memory.sync_paused else "active"
            pending = self.memory.pending_count
            last = self.memory.last_sync
            print(f"Sync status: {paused}")
            print(f"Pending: {pending} records")
            print(f"Last sync: {last.isoformat() if last else 'never'}")
        elif args == "--full":
            self.memory.compact()
            self.memory.flush(force=True)
            print("✓ Full sync complete")
        else:
            count = self.memory.flush(force=True)
            print(f"✓ Synced {count} records")
    
    def _show_memory(self, args: str) -> None:
        """Show memory contents."""
        if args == "--all":
            # Show everything
            entries = self.memory.get_entries()
            summaries = self.memory.get_summaries()
            
            if summaries:
                print("\n📜 Summaries:")
                for s in summaries:
                    print(f"  [{s.timestamp.strftime('%m/%d %H:%M')}] {s.content[:100]}...")
            
            print("\n💬 Entries:")
            for e in entries[:20]:
                role = e.role.title()
                content = e.content[:80].replace("\n", " ")
                print(f"  [{e.timestamp.strftime('%H:%M')}] {role}: {content}...")
        
        elif args.startswith("--search "):
            query = args[9:]
            results = self.memory.search(query, k=10)
            print(f"\n🔍 Search results for '{query}':")
            for e in results:
                role = e.role.title()
                content = e.content[:80].replace("\n", " ")
                print(f"  [{e.timestamp.strftime('%m/%d %H:%M')}] {role}: {content}...")
        
        else:
            # Show recent
            entries = self.memory.get_entries(limit=10)
            print("\n💬 Recent entries:")
            for e in entries:
                role = e.role.title()
                content = e.content[:80].replace("\n", " ")
                print(f"  [{e.timestamp.strftime('%H:%M')}] {role}: {content}...")
            
            if not entries:
                print("  (no entries)")
    
    def _show_memory_stats(self) -> None:
        """Show memory statistics."""
        stats = self.memory.stats()
        print("\n📊 Memory Statistics:")
        print(f"  Entries: {stats['entries']}")
        print(f"  Summaries: {stats['summaries']}")
        print(f"  Checkpoints: {stats['checkpoints']}")
        print(f"  Preferences: {stats['preferences']}")
        print(f"  Total tokens: {stats['total_tokens']}")
        print(f"  Active tokens: {stats['active_tokens']}")
        print(f"  Pending sync: {stats['pending_sync']}")
        print(f"  Sync paused: {stats['sync_paused']}")
        if stats['last_sync']:
            print(f"  Last sync: {stats['last_sync']}")
    
    def _handle_config_command(self, args: str) -> None:
        """Handle config subcommands."""
        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower() if parts else "show"
        
        if subcommand == "show":
            self._show_config()
        elif subcommand == "reload":
            reset_config()
            self.config = PyNextConfig.load(self.project_path)
            self.resolver = ConfigResolver(self.config)
            print("✓ Config reloaded")
        elif subcommand == "resolved":
            self._show_resolved_config()
        else:
            print(f"Unknown config command: {subcommand}")
            print("Available: show, reload, resolved")
    
    def _show_config(self) -> None:
        """Show current configuration."""
        print("\n⚙️  Configuration:")
        print(f"  AI Model: {self.config.ai.model}")
        print(f"  Mode: {self.config.ai.mode}")
        print(f"  Complexity: {self.config.ai.complexity}")
        print(f"  Verbose: {self.config.ai.verbose}")
        print(f"\n  Style:")
        print(f"    Naming: {self.config.style.naming_convention}")
        print(f"    Docstrings: {self.config.style.docstring_style}")
        print(f"    Max line: {self.config.style.max_line_length}")
        print(f"\n  Validation:")
        print(f"    Require docstrings: {self.config.validation.require_docstrings}")
        print(f"    Require type hints: {self.config.validation.require_type_hints}")
        print(f"    Require tests: {self.config.validation.require_tests}")
        
        if self.config.active_mode:
            print(f"\n  Active Mode: {self.config.active_mode}")
        
        if self.config.patterns:
            print(f"\n  Patterns: {len(self.config.patterns)}")
            for name in list(self.config.patterns.keys())[:5]:
                print(f"    - {name}")
    
    def _show_resolved_config(self) -> None:
        """Show resolved configuration for current context."""
        ctx = ConfigContext(
            file_type="",
            intent="chat",
            description="",
            mode=self.state.mode,
            project=self.state.context,
        )
        resolved = self.resolver.resolve_sync(ctx)
        
        print("\n🎯 Resolved Configuration:")
        if resolved.system_prompt:
            print(f"\n  System prompt: {resolved.system_prompt[:100]}...")
        if resolved.prompts:
            print(f"\n  Active prompts: {len(resolved.prompts)}")
            for p in resolved.prompts[:3]:
                print(f"    - {p[:50]}...")
        if resolved.rules:
            print(f"\n  Active rules: {len(resolved.rules)}")
            for r in resolved.rules[:3]:
                print(f"    - {r[:50]}...")
        if resolved.patterns:
            print(f"\n  Matched patterns: {len(resolved.patterns)}")
            for p in resolved.patterns[:3]:
                print(f"    - {p.name}")
    
    async def _create_checkpoint(self, description: str) -> None:
        """Create a manual checkpoint."""
        if not self.state.project_path:
            print("No project to checkpoint")
            return
        
        # Get file hashes
        files_snapshot = {}
        for file in self.state.project_path.rglob("*.py"):
            if ".pynext" not in str(file):
                try:
                    content = file.read_text()
                    import hashlib
                    hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]
                    files_snapshot[str(file.relative_to(self.state.project_path))] = hash_value
                except Exception:
                    pass
        
        cp_id = self.memory.add_checkpoint(
            trigger="user_request",
            description=description or "Manual checkpoint",
            files=files_snapshot,
        )
        print(f"✓ Created checkpoint: {cp_id}")
    
    async def _handle_input(self, user_input: str) -> None:
        """Handle natural language input."""
        # Add to memory
        entry_id = self.memory.add("user", user_input, {})
        
        # Add to session history
        self.state.history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.utcnow().isoformat(),
            "entry_id": entry_id,
        })
        
        # Get relevant context from memory
        memory_context = self.memory.get_relevant_context(user_input, max_tokens=2000)
        
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
        
        # Create checkpoint before generation
        if self.state.project_path and self.state.project_path.exists():
            await self._create_checkpoint("Before new project generation")
        
        # Create plan
        plan = await self.planner.create_plan(description)
        self.state.current_plan = plan
        
        # Show plan
        print("\n" + plan.to_markdown())
        
        # Add assistant response to memory
        response = f"Created plan for: {description}\nFiles: {len(plan.operations)}"
        self.memory.add("assistant", response, {
            "plan_id": id(plan),
            "files": [op.path for op in plan.operations] if plan.operations else [],
        })
        
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
        
        # Create checkpoint before adding feature
        await self._create_checkpoint(f"Before adding: {feature[:50]}")
        
        # Create plan
        plan = await self.planner.plan_feature(
            feature=feature,
            project_path=self.state.project_path,
        )
        self.state.current_plan = plan
        
        if not plan.operations:
            print("⚠️  Could not determine what to create")
            self.memory.add("assistant", f"Could not plan feature: {feature}", {})
            return
        
        # Show plan
        print("\n" + plan.to_markdown())
        
        # Add to memory
        response = f"Planned feature: {feature}\nFiles: {len(plan.operations)}"
        self.memory.add("assistant", response, {
            "plan_id": id(plan),
            "files": [op.path for op in plan.operations],
        })
        
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
            
            # Add to memory
            self.memory.add("assistant", f"Generated {len(result.generated_files)} files successfully", {
                "files": list(result.generated_files.keys()),
                "success": True,
            })
            
            # Create checkpoint after generation
            await self._create_checkpoint(f"After generation: {plan.name}")
            
            await self._analyze_project()  # Refresh context
        else:
            print(f"\n⚠️  Generation completed with issues")
            if result.failed_files:
                print(f"   Failed: {', '.join(result.failed_files)}")
            
            self.memory.add("assistant", f"Generation completed with issues", {
                "files": list(result.generated_files.keys()),
                "failed": result.failed_files,
                "success": False,
            })
        
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
        
        print("\n📋 Memory subcommands:")
        print("  /memory show [--all|--search query]")
        print("  /memory clear")
        print("  /memory flush")
        print("  /memory stats")
        print("  /memory export [markdown|json]")
        print("  /memory compact")
        print("  /memory sync [--pause|--resume|--status|--full]")
        
        print("\n⚙️  Config subcommands:")
        print("  /config show")
        print("  /config reload")
        print("  /config resolved")
        
        print("\n💡 Examples:")
        print("  > Create a blog with user authentication")
        print("  > Add a dark mode toggle")
        print("  > /mode agent")
        print("  > /memory show --search auth")
    
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
            
            # Learn preference
            self.memory.add_preference("mode", mode, confidence=0.8)
            
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
        
        # Memory stats
        stats = self.memory.stats()
        print(f"  Memory: {stats['entries']} entries, {stats['active_tokens']} active tokens")
        
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
