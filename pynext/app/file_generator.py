"""
File Generator - Generates individual files with context.

Uses the knowledge base, configuration, and AI to generate high-quality
PyNext code for each file in a plan.

Features:
- Integrates PyNext knowledge base for accurate code
- Uses config system for prompts and rules
- Applies conditional prompts based on context
- Supports team standards and patterns

Example:
    generator = FileGenerator(config)
    
    code = await generator.generate_file(
        operation=FileOperation(...),
        context=project_context,
        previous_files={"pages/layout.py": "..."},
    )
"""

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .knowledge import get_knowledge, init_knowledge
from .config import PyNextConfig, ConfigResolver, ConfigContext, get_config

logger = logging.getLogger(__name__)


@dataclass
class GeneratedFile:
    """A generated file with metadata."""
    path: str
    content: str
    file_type: str
    imports: List[str]
    dependencies: List[str]


class FileGenerator:
    """
    Generates individual files with context.
    
    Uses the PyNext knowledge base and configuration system
    to provide rich context for AI generation of each file.
    """
    
    def __init__(
        self,
        config: Optional[PyNextConfig] = None,
        project_path: Optional[Path] = None,
    ):
        """
        Initialize file generator.
        
        Args:
            config: PyNext configuration for generation
            project_path: Path to project directory
        """
        self.project_path = project_path or Path.cwd()
        self.config = config or get_config(self.project_path)
        self.resolver = ConfigResolver(self.config)
        self._client = None
        self._knowledge = None
    
    async def _init_knowledge(self):
        """Initialize knowledge base."""
        if self._knowledge is None:
            self._knowledge = await init_knowledge()
        return self._knowledge
    
    def _get_client(self):
        """Get or create AI client."""
        if self._client is None:
            try:
                import anthropic
                import os
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                self._client = anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic package required")
        return self._client
    
    async def generate_file(
        self,
        operation: Any,  # FileOperation
        context: Optional[Any] = None,  # ProjectContext
        previous_files: Optional[Dict[str, str]] = None,
    ) -> GeneratedFile:
        """
        Generate a single file.
        
        Args:
            operation: FileOperation to generate
            context: Project context
            previous_files: Already generated files
        
        Returns:
            GeneratedFile with content
        """
        # Initialize knowledge base
        knowledge = await self._init_knowledge()
        
        # Build config context for this file
        config_context = ConfigContext(
            file_type=operation.file_type,
            intent="generate",
            description=operation.description,
            mode=self.config.ai.mode,
            project=context,
        )
        
        # Resolve config for this context
        resolved_config = self.resolver.resolve_sync(config_context)
        
        # Build context for generation
        generation_context = await self._build_context(
            operation=operation,
            knowledge=knowledge,
            resolved_config=resolved_config,
            context=context,
            previous_files=previous_files or {},
        )
        
        # Generate with AI
        content = await self._generate_with_ai(
            operation=operation,
            generation_context=generation_context,
            resolved_config=resolved_config,
        )
        
        # Apply file header from config
        if self.config.team.file_header:
            header = self.config.substitute_vars(self.config.team.file_header)
            if not content.startswith(header.strip()):
                content = header.strip() + "\n\n" + content
        
        # Extract imports from generated code
        imports = self._extract_imports(content)
        
        return GeneratedFile(
            path=operation.path,
            content=content,
            file_type=operation.file_type,
            imports=imports,
            dependencies=operation.dependencies,
        )
    
    async def _build_context(
        self,
        operation: Any,
        knowledge: Any,  # PyNextKnowledge
        resolved_config: Any,  # ResolvedConfig
        context: Optional[Any],
        previous_files: Dict[str, str],
    ) -> str:
        """Build context for file generation."""
        parts = []
        
        # Add resolved config context (includes system prompt, rules, etc.)
        config_prompt = resolved_config.get_full_prompt(operation.file_type)
        if config_prompt:
            parts.append(config_prompt)
        
        # Get knowledge context based on operation
        task = f"Create a {operation.file_type}: {operation.description}"
        knowledge_context = knowledge.build_file_context(
            file_type=operation.file_type,
            requirements=operation.requirements,
            existing_files=previous_files,
        )
        parts.append(knowledge_context)
        
        # Add matched patterns from config
        if resolved_config.patterns:
            parts.append("\n## Suggested Patterns")
            for pattern in resolved_config.patterns:
                parts.append(f"\n### {pattern.name}")
                parts.append(pattern.description)
                parts.append("```python")
                parts.append(pattern.code)
                parts.append("```")
        
        # Add operation requirements
        if operation.requirements:
            parts.append("\n## File Requirements")
            for key, value in operation.requirements.items():
                parts.append(f"- {key}: {value}")
        
        # Add dependencies info
        if operation.dependencies:
            parts.append("\n## Dependencies")
            parts.append("This file depends on:")
            for dep in operation.dependencies:
                parts.append(f"- {dep}")
                if dep in previous_files:
                    # Show imports from dependency
                    dep_imports = self._extract_imports(previous_files[dep])
                    if dep_imports:
                        parts.append("  Exports: " + ", ".join(dep_imports[:5]))
        
        # Add examples from config
        if operation.file_type == "island" and self.config.examples.good_island:
            parts.append("\n## Example (Good)")
            parts.append("```python")
            parts.append(self.config.examples.good_island)
            parts.append("```")
        
        return "\n".join(parts)
    
    async def _generate_with_ai(
        self,
        operation: Any,
        generation_context: str,
        resolved_config: Any,
    ) -> str:
        """Generate file content with AI."""
        client = self._get_client()
        
        # Build base rules
        base_rules = """
## Output Rules
1. Return ONLY valid Python code
2. Include all necessary imports at the top
3. Use type hints for function parameters
4. Add docstrings for functions and classes
5. Follow PyNext conventions:
   - Use class_ not class for CSS classes
   - Use input_ not input for input elements
   - Signals are read by calling them: count()
   - Signals are written with .set(): count.set(count() + 1)
6. Use Tailwind CSS classes for styling
7. Make the code production-ready
"""
        
        # Add config-specific rules
        style_rules = []
        if self.config.style.naming_convention:
            style_rules.append(f"- Use {self.config.style.naming_convention} for functions and variables")
        if self.config.style.docstring_style:
            style_rules.append(f"- Use {self.config.style.docstring_style} docstring style")
        if self.config.validation.require_type_hints:
            style_rules.append("- All functions MUST have type hints")
        if self.config.validation.forbidden_imports:
            style_rules.append(f"- Never use: {', '.join(self.config.validation.forbidden_imports)}")
        
        if style_rules:
            base_rules += "\n## Style Requirements\n" + "\n".join(style_rules)
        
        # Get suffix from resolved config
        suffix = resolved_config.suffix_prompt if resolved_config.suffix_prompt else ""
        
        prompt = f"""Generate a PyNext {operation.file_type} file.

File: {operation.path}
Description: {operation.description}

{generation_context}

{base_rules}

{suffix}

Return the complete Python code, nothing else."""

        try:
            loop = asyncio.get_event_loop()
            model = self.config.ai.model
            
            def make_call():
                return client.messages.create(
                    model=model,
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}],
                )
            
            response = await loop.run_in_executor(None, make_call)
            result = response.content[0].text
            
            # Extract code from response
            code = self._extract_code(result)
            
            return code
            
        except Exception as e:
            logger.error(f"AI generation failed for {operation.path}: {e}")
            # Return a placeholder
            return self._generate_placeholder(operation)
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from response."""
        # Check for code blocks
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Check for any code block
        code_match = re.search(r'```\n?(.*?)```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Assume entire response is code
        return response.strip()
    
    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        for line in code.split("\n"):
            line = line.strip()
            if line.startswith("import ") or line.startswith("from "):
                imports.append(line)
        return imports
    
    def _generate_placeholder(self, operation: Any) -> str:
        """Generate placeholder code for failed generation."""
        file_type = operation.file_type
        
        # Add file header if configured
        header = ""
        if self.config.team.file_header:
            header = self.config.substitute_vars(self.config.team.file_header.strip()) + "\n\n"
        
        if file_type == "page":
            return f'''{header}"""
{operation.description}

TODO: Complete implementation
"""
from pynext import div, h1, p

def page():
    """Render the page."""
    return div(class_="container mx-auto p-4")(
        h1(class_="text-2xl font-bold")("{operation.path}"),
        p("TODO: Implement {operation.description}"),
    )
'''
        elif file_type == "component":
            name = Path(operation.path).stem
            prefix = self.config.team.component_prefix
            component_name = f"{prefix}{name}" if prefix else name
            return f'''{header}"""
{operation.description}
"""
from pynext import div

def {component_name}(**props):
    """TODO: Implement component."""
    return div(class_="p-4")(
        "TODO: {operation.description}"
    )
'''
        elif file_type == "island":
            name = Path(operation.path).stem
            prefix = self.config.team.component_prefix
            component_name = f"{prefix}{name}" if prefix else name
            return f'''{header}"""
{operation.description}
"""
from pynext import div, button
from pynext import Signal
from pynext.islands import island

@island
def {component_name}():
    """TODO: Implement interactive component."""
    return div(class_="p-4")(
        "TODO: {operation.description}"
    )
'''
        elif file_type == "model":
            name = Path(operation.path).stem.title()
            return f'''{header}"""
{operation.description}
"""
from pynext.db import Table, Column, types

class {name}(Table):
    """TODO: Define model fields."""
    id = Column(types.Integer, primary_key=True)
    created_at = Column(types.DateTime, default="now()")
    updated_at = Column(types.DateTime, default="now()", on_update="now()")
    # TODO: Add fields
'''
        elif file_type == "api":
            return f'''{header}"""
{operation.description}
"""
from pynext.api import api, Request, Response

@api
async def GET(request: Request):
    """TODO: Implement GET handler."""
    return Response.json({{"message": "TODO"}})

@api
async def POST(request: Request):
    """TODO: Implement POST handler."""
    data = await request.json()
    return Response.json({{"received": data}})
'''
        elif file_type == "layout":
            return f'''{header}"""
Application layout.
"""
from pynext import div, header, main, footer, nav, a

def layout(children):
    """Wrap pages with layout."""
    return div(class_="min-h-screen flex flex-col")(
        header(class_="bg-gray-800 text-white p-4")(
            nav(class_="container mx-auto flex justify-between")(
                a(href="/", class_="font-bold")("App"),
            ),
        ),
        main(class_="flex-1 container mx-auto p-4")(
            children,
        ),
        footer(class_="bg-gray-100 p-4 text-center")(
            "© 2024",
        ),
    )
'''
        else:
            return f'''{header}"""
{operation.description}

TODO: Complete implementation
"""

# TODO: Implement {operation.path}
'''


class BatchFileGenerator:
    """Generate multiple files in batch with shared context."""
    
    def __init__(
        self,
        config: Optional[PyNextConfig] = None,
        project_path: Optional[Path] = None,
    ):
        """Initialize batch generator."""
        self.generator = FileGenerator(config, project_path)
    
    async def generate_batch(
        self,
        operations: List[Any],  # List[FileOperation]
        context: Optional[Any] = None,
    ) -> Dict[str, GeneratedFile]:
        """
        Generate multiple files in order.
        
        Args:
            operations: Operations to process in order
            context: Project context
        
        Returns:
            Dict mapping path to generated file
        """
        generated_files: Dict[str, GeneratedFile] = {}
        
        for operation in operations:
            # Build context from previously generated files
            previous_files = {
                path: gf.content
                for path, gf in generated_files.items()
            }
            
            # Generate file
            generated = await self.generator.generate_file(
                operation=operation,
                context=context,
                previous_files=previous_files,
            )
            
            generated_files[operation.path] = generated
        
        return generated_files
