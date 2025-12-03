"""
PyNext App Builder - AI-powered application scaffolding.

Build entire applications from natural language descriptions with:
- Plan/Agent/Ask modes (like Cursor)
- Smart context retrieval (RAG for PyNext)
- Interactive sessions
- Feature addition to existing projects

Example:
    # From CLI
    pynext app new "task manager with auth and real-time updates"
    pynext app add "dark mode toggle"
    pynext app chat
    
    # From Python
    from pynext.app import AppGenerator
    
    generator = AppGenerator()
    result = await generator.new_app(
        "e-commerce site with product catalog",
        output_dir=Path("./my-store"),
        mode="plan",
        complexity="medium",
    )
"""

from .generator import AppGenerator, GenerationResult
from .planner import AppPlanner, AppPlan, FileOperation
from .context import ContextAnalyzer, ProjectContext
from .session import AppSession
from .progress import ProgressTracker
from .rollback import RollbackManager

__all__ = [
    "AppGenerator",
    "GenerationResult", 
    "AppPlanner",
    "AppPlan",
    "FileOperation",
    "ContextAnalyzer",
    "ProjectContext",
    "AppSession",
    "ProgressTracker",
    "RollbackManager",
]

