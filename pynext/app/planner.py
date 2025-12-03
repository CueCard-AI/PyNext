"""
App Planner - Creates plans for application generation.

Analyzes requirements and creates a structured plan with:
- Files to create/modify
- Dependencies between files
- Estimated complexity
- Required packages

Example:
    planner = AppPlanner(config)
    
    plan = await planner.create_plan(
        "task manager with auth and real-time updates",
        complexity="auto",
    )
    
    print(plan.to_markdown())
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import logging

logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Type of file operation."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


@dataclass
class FileOperation:
    """
    A single file operation in the plan.
    
    Attributes:
        action: create, modify, or delete
        path: File path relative to project root
        description: What this file does
        dependencies: Files that must exist first
        estimated_lines: Estimated lines of code
        file_type: Type of file (page, component, api, etc.)
        requirements: Specific requirements for this file
    """
    action: OperationType
    path: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    estimated_lines: int = 50
    file_type: str = "unknown"
    requirements: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "action": self.action.value,
            "path": self.path,
            "description": self.description,
            "dependencies": self.dependencies,
            "estimated_lines": self.estimated_lines,
            "file_type": self.file_type,
            "requirements": self.requirements,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileOperation":
        """Create from dictionary."""
        return cls(
            action=OperationType(data["action"]),
            path=data["path"],
            description=data["description"],
            dependencies=data.get("dependencies", []),
            estimated_lines=data.get("estimated_lines", 50),
            file_type=data.get("file_type", "unknown"),
            requirements=data.get("requirements", {}),
        )


@dataclass
class AppPlan:
    """
    Complete plan for application generation.
    
    Attributes:
        name: Application name
        description: What the app does
        complexity: minimal, small, medium, large, enterprise
        operations: List of file operations
        estimated_time: Estimated generation time
        warnings: Any warnings or considerations
        packages: Required packages
        created_at: When plan was created
    """
    name: str
    description: str
    complexity: str
    operations: List[FileOperation]
    estimated_time: str = "1-2 minutes"
    warnings: List[str] = field(default_factory=list)
    packages: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "complexity": self.complexity,
            "operations": [op.to_dict() for op in self.operations],
            "estimated_time": self.estimated_time,
            "warnings": self.warnings,
            "packages": self.packages,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppPlan":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            complexity=data["complexity"],
            operations=[FileOperation.from_dict(op) for op in data["operations"]],
            estimated_time=data.get("estimated_time", "1-2 minutes"),
            warnings=data.get("warnings", []),
            packages=data.get("packages", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
        )
    
    def to_markdown(self) -> str:
        """Format plan as markdown for display."""
        lines = [
            f"# App Plan: {self.name}",
            "",
            f"**Description:** {self.description}",
            f"**Complexity:** {self.complexity} ({len(self.operations)} files)",
            f"**Estimated Time:** {self.estimated_time}",
            "",
            "## Files to Create",
            "",
        ]
        
        # Group by action
        creates = [op for op in self.operations if op.action == OperationType.CREATE]
        modifies = [op for op in self.operations if op.action == OperationType.MODIFY]
        
        for i, op in enumerate(creates, 1):
            icon = "✨"
            lines.append(f"{i}. {icon} `{op.path}` - {op.description}")
        
        if modifies:
            lines.append("")
            lines.append("## Files to Modify")
            lines.append("")
            for i, op in enumerate(modifies, 1):
                icon = "📝"
                lines.append(f"{i}. {icon} `{op.path}` - {op.description}")
        
        if self.packages:
            lines.append("")
            lines.append("## Required Packages")
            lines.append("")
            for pkg in self.packages:
                lines.append(f"- {pkg}")
        
        if self.warnings:
            lines.append("")
            lines.append("## ⚠️ Warnings")
            lines.append("")
            for warning in self.warnings:
                lines.append(f"- {warning}")
        
        return "\n".join(lines)
    
    def get_ordered_operations(self) -> List[FileOperation]:
        """Get operations in dependency order."""
        # Build dependency graph
        graph = {op.path: set(op.dependencies) for op in self.operations}
        op_map = {op.path: op for op in self.operations}
        
        # Topological sort
        ordered = []
        visited = set()
        
        def visit(path: str):
            if path in visited:
                return
            visited.add(path)
            
            for dep in graph.get(path, []):
                if dep in op_map:
                    visit(dep)
            
            if path in op_map:
                ordered.append(op_map[path])
        
        for path in graph:
            visit(path)
        
        return ordered


class AppPlanner:
    """
    Creates plans for application generation.
    
    Uses AI to analyze requirements and create a structured
    plan for generating the application.
    """
    
    # Complexity configurations
    COMPLEXITY_CONFIG = {
        "minimal": {"max_files": 5, "features": ["basic"]},
        "small": {"max_files": 10, "features": ["basic", "forms"]},
        "medium": {"max_files": 30, "features": ["basic", "forms", "auth", "database"]},
        "large": {"max_files": 50, "features": ["basic", "forms", "auth", "database", "api", "realtime"]},
        "enterprise": {"max_files": 100, "features": ["all"]},
    }
    
    # Common app structures
    APP_TEMPLATES = {
        "blog": {
            "files": [
                ("pages/index.py", "page", "Home page with post list"),
                ("pages/post/[slug].py", "page", "Post detail page"),
                ("pages/admin/index.py", "page", "Admin dashboard"),
                ("models/post.py", "model", "Post database model"),
                ("api/posts.py", "api", "Posts CRUD API"),
            ],
            "packages": ["pynext[db]"],
        },
        "saas": {
            "files": [
                ("pages/index.py", "page", "Landing page"),
                ("pages/login.py", "page", "Login page"),
                ("pages/signup.py", "page", "Signup page"),
                ("pages/dashboard/index.py", "page", "User dashboard"),
                ("pages/dashboard/settings.py", "page", "Settings page"),
                ("models/user.py", "model", "User model"),
                ("middleware/auth.py", "middleware", "Auth middleware"),
                ("api/users.py", "api", "Users API"),
            ],
            "packages": ["pynext[db]", "pynext[auth]"],
        },
        "ecommerce": {
            "files": [
                ("pages/index.py", "page", "Product listing"),
                ("pages/product/[id].py", "page", "Product detail"),
                ("pages/cart.py", "page", "Shopping cart"),
                ("pages/checkout.py", "page", "Checkout flow"),
                ("models/product.py", "model", "Product model"),
                ("models/order.py", "model", "Order model"),
                ("islands/Cart.py", "island", "Cart component"),
                ("api/products.py", "api", "Products API"),
                ("api/orders.py", "api", "Orders API"),
            ],
            "packages": ["pynext[db]", "pynext[auth]"],
        },
    }
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize planner.
        
        Args:
            config: AIConfig for AI calls
        """
        self.config = config
        self._client = None
    
    def _get_client(self):
        """Get or create AI client."""
        if self._client is None:
            try:
                import anthropic
                import os
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if self.config and hasattr(self.config, 'api_key'):
                    api_key = self.config.api_key or api_key
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic package required")
        return self._client
    
    async def create_plan(
        self,
        description: str,
        complexity: str = "auto",
        existing_project: Optional[Path] = None,
    ) -> AppPlan:
        """
        Create a plan for a new application.
        
        Args:
            description: Natural language description
            complexity: minimal, small, medium, large, enterprise, or auto
            existing_project: Path to existing project (for add feature)
        
        Returns:
            AppPlan with ordered file operations
        """
        # Determine complexity
        if complexity == "auto":
            complexity = self._estimate_complexity(description)
        
        # Check if matches a template
        template = self._match_template(description)
        
        if template:
            # Use template-based planning
            plan = self._plan_from_template(template, description, complexity)
        else:
            # Use AI planning
            plan = await self._plan_with_ai(description, complexity, existing_project)
        
        return plan
    
    async def plan_feature(
        self,
        feature: str,
        project_path: Path,
    ) -> AppPlan:
        """
        Plan adding a feature to existing project.
        
        Args:
            feature: Feature description
            project_path: Path to existing project
        
        Returns:
            AppPlan for the feature addition
        """
        # Analyze existing project
        from .context import ContextAnalyzer
        analyzer = ContextAnalyzer()
        context = await analyzer.analyze(project_path)
        
        # Plan feature with context
        plan = await self._plan_feature_with_ai(feature, context)
        
        return plan
    
    def _estimate_complexity(self, description: str) -> str:
        """Estimate complexity from description."""
        desc_lower = description.lower()
        
        # Count feature indicators
        features = 0
        
        if any(w in desc_lower for w in ["auth", "login", "user"]):
            features += 2
        if any(w in desc_lower for w in ["database", "store", "save"]):
            features += 2
        if any(w in desc_lower for w in ["api", "endpoint", "rest"]):
            features += 1
        if any(w in desc_lower for w in ["realtime", "live", "websocket"]):
            features += 2
        if any(w in desc_lower for w in ["dashboard", "admin"]):
            features += 2
        if any(w in desc_lower for w in ["cart", "payment", "checkout"]):
            features += 3
        
        # Base complexity on word count and features
        word_count = len(desc_lower.split())
        
        if features >= 6 or word_count > 50:
            return "large"
        elif features >= 4 or word_count > 30:
            return "medium"
        elif features >= 2 or word_count > 15:
            return "small"
        else:
            return "minimal"
    
    def _match_template(self, description: str) -> Optional[str]:
        """Match description to a template."""
        desc_lower = description.lower()
        
        if any(w in desc_lower for w in ["blog", "posts", "articles"]):
            return "blog"
        if any(w in desc_lower for w in ["saas", "subscription", "tenant"]):
            return "saas"
        if any(w in desc_lower for w in ["ecommerce", "shop", "store", "cart", "product"]):
            return "ecommerce"
        
        return None
    
    def _plan_from_template(
        self,
        template: str,
        description: str,
        complexity: str,
    ) -> AppPlan:
        """Create plan from template."""
        template_config = self.APP_TEMPLATES.get(template, {})
        
        operations = []
        for path, file_type, desc in template_config.get("files", []):
            operations.append(FileOperation(
                action=OperationType.CREATE,
                path=path,
                description=desc,
                file_type=file_type,
                estimated_lines=self._estimate_lines(file_type),
            ))
        
        # Add layout
        operations.insert(0, FileOperation(
            action=OperationType.CREATE,
            path="pages/layout.py",
            description="Application layout",
            file_type="layout",
            estimated_lines=50,
        ))
        
        # Determine dependencies
        self._add_dependencies(operations)
        
        # Extract app name
        name = description.split()[0].lower().replace(" ", "-")
        if len(name) < 3:
            name = template
        
        return AppPlan(
            name=name,
            description=description,
            complexity=complexity,
            operations=operations,
            estimated_time=self._estimate_time(len(operations)),
            packages=template_config.get("packages", []),
        )
    
    async def _plan_with_ai(
        self,
        description: str,
        complexity: str,
        existing_project: Optional[Path],
    ) -> AppPlan:
        """Create plan using AI."""
        client = self._get_client()
        
        config = self.COMPLEXITY_CONFIG.get(complexity, self.COMPLEXITY_CONFIG["medium"])
        
        prompt = f"""Create a file structure plan for a PyNext application.

Description: {description}
Complexity: {complexity} (max {config['max_files']} files)

PyNext uses:
- pages/ for routes (pages/index.py -> /, pages/about.py -> /about)
- pages/[param].py for dynamic routes
- components/ for reusable components
- islands/ for interactive components
- models/ for database models
- api/ for API routes
- actions/ for server actions
- middleware/ for middleware

Return a JSON object with:
{{
    "name": "app-name",
    "files": [
        {{"path": "pages/index.py", "type": "page", "description": "..."}},
        ...
    ],
    "packages": ["pynext[db]", ...]
}}

Only return valid JSON, no other text."""

        try:
            loop = asyncio.get_event_loop()
            
            def make_call():
                return client.messages.create(
                    model=getattr(self.config, 'model', 'claude-sonnet-4-20250514'),
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}],
                )
            
            response = await loop.run_in_executor(None, make_call)
            result = response.content[0].text
            
            # Parse JSON
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                
                operations = []
                for file_info in data.get("files", []):
                    operations.append(FileOperation(
                        action=OperationType.CREATE,
                        path=file_info["path"],
                        description=file_info.get("description", ""),
                        file_type=file_info.get("type", "unknown"),
                        estimated_lines=self._estimate_lines(file_info.get("type", "unknown")),
                    ))
                
                self._add_dependencies(operations)
                
                return AppPlan(
                    name=data.get("name", "app"),
                    description=description,
                    complexity=complexity,
                    operations=operations,
                    estimated_time=self._estimate_time(len(operations)),
                    packages=data.get("packages", []),
                )
        
        except Exception as e:
            logger.warning(f"AI planning failed: {e}, using default")
        
        # Fallback to basic plan
        return self._create_basic_plan(description, complexity)
    
    async def _plan_feature_with_ai(
        self,
        feature: str,
        context: Any,  # ProjectContext
    ) -> AppPlan:
        """Plan a feature with project context."""
        client = self._get_client()
        
        existing_files = "\n".join([
            f"- {p}" for p in context.pages + context.components
        ])
        
        prompt = f"""Plan adding a feature to an existing PyNext project.

Feature: {feature}

Existing files:
{existing_files}

Return JSON with files to create or modify:
{{
    "files": [
        {{"action": "create", "path": "...", "type": "...", "description": "..."}},
        {{"action": "modify", "path": "...", "type": "...", "description": "..."}}
    ],
    "packages": []
}}

Only return valid JSON."""

        try:
            loop = asyncio.get_event_loop()
            
            def make_call():
                return client.messages.create(
                    model=getattr(self.config, 'model', 'claude-sonnet-4-20250514'),
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}],
                )
            
            response = await loop.run_in_executor(None, make_call)
            result = response.content[0].text
            
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                data = json.loads(json_match.group())
                
                operations = []
                for file_info in data.get("files", []):
                    action = OperationType.CREATE if file_info.get("action") == "create" else OperationType.MODIFY
                    operations.append(FileOperation(
                        action=action,
                        path=file_info["path"],
                        description=file_info.get("description", ""),
                        file_type=file_info.get("type", "unknown"),
                    ))
                
                return AppPlan(
                    name="feature",
                    description=feature,
                    complexity="small",
                    operations=operations,
                    packages=data.get("packages", []),
                )
        
        except Exception as e:
            logger.warning(f"Feature planning failed: {e}")
        
        return AppPlan(
            name="feature",
            description=feature,
            complexity="minimal",
            operations=[],
            warnings=["Could not generate plan automatically"],
        )
    
    def _create_basic_plan(self, description: str, complexity: str) -> AppPlan:
        """Create a basic fallback plan."""
        operations = [
            FileOperation(
                action=OperationType.CREATE,
                path="pages/layout.py",
                description="Application layout",
                file_type="layout",
            ),
            FileOperation(
                action=OperationType.CREATE,
                path="pages/index.py",
                description="Home page",
                file_type="page",
                dependencies=["pages/layout.py"],
            ),
        ]
        
        return AppPlan(
            name="app",
            description=description,
            complexity=complexity,
            operations=operations,
            warnings=["Basic plan - consider providing more details"],
        )
    
    def _add_dependencies(self, operations: List[FileOperation]) -> None:
        """Add dependencies between operations."""
        # Layout should be created first
        layout_paths = [op.path for op in operations if "layout" in op.path]
        
        # Pages depend on layout
        for op in operations:
            if op.file_type == "page" and op.path not in layout_paths:
                for layout in layout_paths:
                    if layout not in op.dependencies:
                        op.dependencies.append(layout)
        
        # API routes depend on models
        model_paths = [op.path for op in operations if op.file_type == "model"]
        for op in operations:
            if op.file_type == "api":
                for model in model_paths:
                    if model not in op.dependencies:
                        op.dependencies.append(model)
    
    def _estimate_lines(self, file_type: str) -> int:
        """Estimate lines of code for file type."""
        estimates = {
            "page": 50,
            "component": 30,
            "island": 60,
            "model": 25,
            "api": 70,
            "action": 40,
            "middleware": 35,
            "layout": 50,
        }
        return estimates.get(file_type, 40)
    
    def _estimate_time(self, num_files: int) -> str:
        """Estimate generation time."""
        if num_files <= 5:
            return "30 seconds - 1 minute"
        elif num_files <= 15:
            return "1-2 minutes"
        elif num_files <= 30:
            return "2-4 minutes"
        else:
            return "4-8 minutes"

