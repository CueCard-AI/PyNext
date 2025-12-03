"""
Configuration System - Hierarchical config with conditional prompts and patterns.

Supports:
- Global, project, and feature-level configs
- Variables with computed values
- Named modes (prototype, production, strict)
- Conditional prompts evaluated by Python or LLM
- Custom patterns with templates
- Flexible rules and validation

Example:
    config = PyNextConfig.load(project_path=Path("."))
    
    # Get resolved config for a specific context
    resolver = ConfigResolver(config, llm_client)
    resolved = await resolver.resolve(ConfigContext(
        file_type="api",
        intent="add_feature",
        description="user authentication",
    ))
    
    # Use in generation
    prompt = resolved.get_system_prompt()
"""

import ast
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# Config Data Classes
# =============================================================================

@dataclass
class AIPreferences:
    """AI generation preferences."""
    model: str = "claude-sonnet-4-20250514"
    mode: str = "plan"  # plan, agent, ask
    complexity: str = "auto"
    max_thoughts: int = 5
    verbose: bool = False
    temperature: float = 0.7
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIPreferences":
        """Create from dict, ignoring unknown fields."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class CodeStyle:
    """Code style preferences."""
    naming_convention: str = "snake_case"
    class_naming: str = "PascalCase"
    max_line_length: int = 88
    quote_style: str = "double"
    trailing_comma: bool = True
    docstring_style: str = "google"
    indent_size: int = 4
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeStyle":
        """Create from dict, ignoring unknown fields."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class ValidationRules:
    """Code validation rules."""
    require_docstrings: bool = True
    require_type_hints: bool = True
    require_tests: bool = False
    max_function_lines: int = 50
    max_file_lines: int = 500
    forbidden_imports: List[str] = field(default_factory=list)
    required_imports: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationRules":
        """Create from dict, ignoring unknown fields."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class TeamStandards:
    """Team-specific standards."""
    component_prefix: str = ""
    file_header: str = ""
    required_patterns: List[str] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TeamStandards":
        """Create from dict, ignoring unknown fields."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class PromptConfig:
    """Flexible prompt configuration."""
    system: str = ""  # Prepended to all generations
    suffix: str = ""  # Appended to all generations
    context: str = ""  # Project/domain context
    
    # Per-file-type prompts
    page: Dict[str, str] = field(default_factory=dict)
    island: Dict[str, str] = field(default_factory=dict)
    api: Dict[str, str] = field(default_factory=dict)
    model: Dict[str, str] = field(default_factory=dict)
    action: Dict[str, str] = field(default_factory=dict)
    component: Dict[str, str] = field(default_factory=dict)
    layout: Dict[str, str] = field(default_factory=dict)
    middleware: Dict[str, str] = field(default_factory=dict)
    util: Dict[str, str] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PromptConfig":
        """Create from dict."""
        return cls(
            system=data.get("system", ""),
            suffix=data.get("suffix", ""),
            context=data.get("context", ""),
            page=data.get("page", {}),
            island=data.get("island", {}),
            api=data.get("api", {}),
            model=data.get("model", {}),
            action=data.get("action", {}),
            component=data.get("component", {}),
            layout=data.get("layout", {}),
            middleware=data.get("middleware", {}),
            util=data.get("util", {}),
        )
    
    def get_for_type(self, file_type: str) -> Dict[str, str]:
        """Get prompts for a file type."""
        return getattr(self, file_type, {})


@dataclass
class Pattern:
    """A reusable code pattern."""
    name: str
    description: str = ""
    code: str = ""
    tags: List[str] = field(default_factory=list)
    deps: List[str] = field(default_factory=list)
    when: str = ""  # Python condition
    when_llm: str = ""  # LLM-evaluated condition
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "Pattern":
        """Create from dict."""
        return cls(
            name=name,
            description=data.get("description", ""),
            code=data.get("code", ""),
            tags=data.get("tags", []),
            deps=data.get("deps", []),
            when=data.get("when", ""),
            when_llm=data.get("when_llm", ""),
        )
    
    def render(self, **variables: str) -> str:
        """Render the pattern with variables."""
        code = self.code
        for name, value in variables.items():
            code = code.replace(f"${{{name}}}", value)
        return code


@dataclass
class Conditional:
    """A conditional config block."""
    priority: int = 50
    when: str = ""  # Python condition
    when_llm: str = ""  # LLM-evaluated condition
    prompt: str = ""
    pattern: str = ""  # Pattern name to suggest
    rules: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conditional":
        """Create from dict."""
        return cls(
            priority=data.get("priority", 50),
            when=data.get("when", ""),
            when_llm=data.get("when_llm", ""),
            prompt=data.get("prompt", ""),
            pattern=data.get("pattern", ""),
            rules=data.get("rules", ""),
        )


@dataclass
class RulesConfig:
    """Custom rules and constraints."""
    custom: str = ""  # Freeform rules text
    always: str = ""  # Always-applied rules
    naming: Dict[str, str] = field(default_factory=dict)
    structure: Dict[str, List[str]] = field(default_factory=dict)
    conditionals: List[Conditional] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RulesConfig":
        """Create from dict."""
        conditionals = []
        for cond_data in data.get("conditional", []):
            conditionals.append(Conditional.from_dict(cond_data))
        
        always_data = data.get("always", {})
        
        return cls(
            custom=data.get("custom", ""),
            always=always_data.get("custom", "") if isinstance(always_data, dict) else "",
            naming=data.get("naming", {}),
            structure=data.get("structure", {}),
            conditionals=conditionals,
        )


@dataclass
class ExamplesConfig:
    """Few-shot examples for AI."""
    good_island: str = ""
    bad_island: str = ""
    good_api: str = ""
    bad_api: str = ""
    good_component: str = ""
    bad_component: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExamplesConfig":
        """Create from dict."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class ModeConfig:
    """A named mode configuration bundle."""
    description: str = ""
    extends: str = ""  # Parent mode to inherit from
    ai: Optional[AIPreferences] = None
    style: Optional[CodeStyle] = None
    validation: Optional[ValidationRules] = None
    prompts: Optional[PromptConfig] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModeConfig":
        """Create from dict."""
        return cls(
            description=data.get("description", ""),
            extends=data.get("extends", ""),
            ai=AIPreferences.from_dict(data["ai"]) if "ai" in data else None,
            style=CodeStyle.from_dict(data["style"]) if "style" in data else None,
            validation=ValidationRules.from_dict(data["validation"]) if "validation" in data else None,
            prompts=PromptConfig.from_dict(data["prompts"]) if "prompts" in data else None,
        )


@dataclass
class MemoryConfig:
    """Memory sync configuration."""
    sync_mode: str = "incremental"
    sync_on: List[str] = field(default_factory=lambda: ["assistant_response", "checkpoint", "exit"])
    sync_interval: int = 0
    sync_batch_size: int = 5
    sync_entries: bool = True
    sync_summaries: bool = True
    sync_checkpoints: bool = True
    sync_preferences: bool = True
    exclude_roles: List[str] = field(default_factory=list)
    min_content_length: int = 0
    max_entries_in_memory: int = 1000
    max_file_size_mb: int = 50
    rotate_files: bool = True
    max_rotated_files: int = 5
    compress_on_sync: bool = False
    compress_threshold_mb: int = 10
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryConfig":
        """Create from dict, ignoring unknown fields."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


# =============================================================================
# Main Config Class
# =============================================================================

@dataclass
class PyNextConfig:
    """
    Complete PyNext configuration.
    
    Loaded from:
    1. Global: ~/.config/pynext/config.toml
    2. Project: ./pynext.toml or ./.pynext/config.toml
    3. Environment variables
    4. CLI arguments
    """
    
    ai: AIPreferences = field(default_factory=AIPreferences)
    style: CodeStyle = field(default_factory=CodeStyle)
    validation: ValidationRules = field(default_factory=ValidationRules)
    team: TeamStandards = field(default_factory=TeamStandards)
    prompts: PromptConfig = field(default_factory=PromptConfig)
    rules: RulesConfig = field(default_factory=RulesConfig)
    examples: ExamplesConfig = field(default_factory=ExamplesConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    
    # Variables
    vars: Dict[str, str] = field(default_factory=dict)
    vars_computed: Dict[str, str] = field(default_factory=dict)
    
    # Modes
    modes: Dict[str, ModeConfig] = field(default_factory=dict)
    active_mode: str = ""
    
    # Patterns
    patterns: Dict[str, Pattern] = field(default_factory=dict)
    
    # Conditionals
    conditionals: List[Conditional] = field(default_factory=list)
    
    @classmethod
    def load(cls, project_path: Optional[Path] = None) -> "PyNextConfig":
        """
        Load merged config from global + project + env.
        
        Args:
            project_path: Project directory path
            
        Returns:
            Merged configuration
        """
        config = cls()
        project_path = project_path or Path.cwd()
        
        # 1. Load global config
        global_config = Path.home() / ".config" / "pynext" / "config.toml"
        if global_config.exists():
            config._merge_from_file(global_config)
        
        # 2. Load project config
        project_configs = [
            project_path / "pynext.toml",
            project_path / ".pynext" / "config.toml",
        ]
        for config_file in project_configs:
            if config_file.exists():
                config._merge_from_file(config_file)
                break
        
        # 3. Apply environment overrides
        config._apply_env_overrides()
        
        # 4. Resolve variables
        config._resolve_variables()
        
        return config
    
    def _merge_from_file(self, config_file: Path) -> None:
        """Merge config from a TOML file."""
        if tomllib is None:
            logger.warning("tomllib not available, skipping config file")
            return
        
        try:
            with open(config_file, "rb") as f:
                data = tomllib.load(f)
            
            # AI settings
            if "ai" in data:
                self.ai = AIPreferences.from_dict(data["ai"])
            
            # Style
            if "style" in data:
                self.style = CodeStyle.from_dict(data["style"])
            
            # Validation
            if "validation" in data:
                self.validation = ValidationRules.from_dict(data["validation"])
            
            # Team
            if "team" in data:
                self.team = TeamStandards.from_dict(data["team"])
            
            # Prompts
            if "prompts" in data:
                self.prompts = PromptConfig.from_dict(data["prompts"])
            
            # Rules
            if "rules" in data:
                self.rules = RulesConfig.from_dict(data["rules"])
            
            # Examples
            if "examples" in data:
                self.examples = ExamplesConfig.from_dict(data["examples"])
            
            # Memory
            if "memory" in data:
                self.memory = MemoryConfig.from_dict(data["memory"])
            
            # Variables
            if "vars" in data:
                self.vars.update(data["vars"])
                if "computed" in data["vars"]:
                    self.vars_computed.update(data["vars"]["computed"])
            
            # Modes
            if "mode" in data:
                for mode_name, mode_data in data["mode"].items():
                    self.modes[mode_name] = ModeConfig.from_dict(mode_data)
            
            # Patterns
            if "patterns" in data:
                for pattern_name, pattern_data in data["patterns"].items():
                    self.patterns[pattern_name] = Pattern.from_dict(pattern_name, pattern_data)
            
            # Conditionals
            if "conditional" in data:
                for cond_data in data["conditional"]:
                    self.conditionals.append(Conditional.from_dict(cond_data))
            
            # Active mode
            if "active_mode" in data:
                self.active_mode = data["active_mode"]
            
            logger.info(f"Loaded config from {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load config from {config_file}: {e}")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_mappings = {
            "PYNEXT_AI_MODEL": ("ai", "model"),
            "PYNEXT_AI_MODE": ("ai", "mode"),
            "PYNEXT_AI_VERBOSE": ("ai", "verbose"),
            "PYNEXT_MODE": ("", "active_mode"),
            "ANTHROPIC_MODEL": ("ai", "model"),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                if section:
                    obj = getattr(self, section)
                    if hasattr(obj, key):
                        # Convert type
                        current = getattr(obj, key)
                        if isinstance(current, bool):
                            value = value.lower() in ("true", "1", "yes")
                        elif isinstance(current, int):
                            value = int(value)
                        elif isinstance(current, float):
                            value = float(value)
                        setattr(obj, key, value)
                else:
                    setattr(self, key, value)
    
    def _resolve_variables(self) -> None:
        """Resolve all variables including computed ones."""
        # First, handle environment variable fallbacks
        resolved = {}
        for name, value in self.vars.items():
            if isinstance(value, str) and "${" in value:
                # Check for env fallback pattern: ${VAR | default}
                match = re.match(r"\$\{(\w+)\s*\|\s*(.+)\}", value)
                if match:
                    env_name, default = match.groups()
                    resolved[name] = os.environ.get(env_name, default)
                else:
                    resolved[name] = value
            else:
                resolved[name] = value
        
        self.vars = resolved
        
        # Then compute derived values
        for name, expr in self.vars_computed.items():
            try:
                # Safe evaluation with only vars as context
                result = eval(expr, {"__builtins__": {}}, self.vars)
                self.vars[name] = str(result)
            except Exception as e:
                logger.warning(f"Failed to compute variable {name}: {e}")
    
    def substitute_vars(self, text: str) -> str:
        """Replace ${var} with resolved values."""
        for name, value in self.vars.items():
            text = text.replace(f"${{{name}}}", str(value))
        return text
    
    def get_mode(self, mode_name: str) -> Optional[ModeConfig]:
        """Get a mode configuration."""
        return self.modes.get(mode_name)
    
    def get_pattern(self, pattern_name: str) -> Optional[Pattern]:
        """Get a pattern by name."""
        return self.patterns.get(pattern_name)
    
    def get_patterns_by_tags(self, tags: List[str]) -> List[Pattern]:
        """Get patterns matching any of the given tags."""
        matching = []
        for pattern in self.patterns.values():
            if any(tag in pattern.tags for tag in tags):
                matching.append(pattern)
        return matching
    
    def to_prompt(self) -> str:
        """
        Format config as context for LLM prompts.
        
        Returns:
            Formatted string to include in system prompt
        """
        parts = []
        
        # System prompt
        if self.prompts.system:
            parts.append(self.prompts.system)
        
        # Context
        if self.prompts.context:
            parts.append(f"## Project Context\n{self.prompts.context}")
        
        # Style rules
        style_rules = []
        if self.style.naming_convention:
            style_rules.append(f"- Use {self.style.naming_convention} for functions/variables")
        if self.style.class_naming:
            style_rules.append(f"- Use {self.style.class_naming} for classes")
        if self.style.docstring_style:
            style_rules.append(f"- Use {self.style.docstring_style} docstring style")
        if self.style.max_line_length:
            style_rules.append(f"- Max line length: {self.style.max_line_length}")
        
        if style_rules:
            parts.append("## Code Style\n" + "\n".join(style_rules))
        
        # Validation rules
        val_rules = []
        if self.validation.require_docstrings:
            val_rules.append("- All functions must have docstrings")
        if self.validation.require_type_hints:
            val_rules.append("- All functions must have type hints")
        if self.validation.forbidden_imports:
            val_rules.append(f"- Forbidden imports: {', '.join(self.validation.forbidden_imports)}")
        
        if val_rules:
            parts.append("## Validation Rules\n" + "\n".join(val_rules))
        
        # Team standards
        if self.team.file_header:
            parts.append(f"## File Header\n{self.team.file_header}")
        
        # Custom rules
        if self.rules.always:
            parts.append(f"## Always Apply\n{self.rules.always}")
        if self.rules.custom:
            parts.append(f"## Custom Rules\n{self.rules.custom}")
        
        return "\n\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "ai": asdict(self.ai),
            "style": asdict(self.style),
            "validation": asdict(self.validation),
            "team": asdict(self.team),
            "prompts": asdict(self.prompts),
            "rules": {
                "custom": self.rules.custom,
                "always": self.rules.always,
                "naming": self.rules.naming,
                "structure": self.rules.structure,
            },
            "memory": asdict(self.memory),
            "vars": self.vars,
            "active_mode": self.active_mode,
            "patterns": {name: asdict(p) for name, p in self.patterns.items()},
        }


# =============================================================================
# Config Context
# =============================================================================

@dataclass
class ConfigContext:
    """Context available for condition evaluation."""
    file_type: str = ""
    intent: str = ""  # new_app, add_feature, refactor
    description: str = ""
    mode: str = "production"
    complexity: str = "auto"
    project: Optional[Any] = None  # ProjectContext
    user_command: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for expression evaluation."""
        project_dict = {}
        if self.project:
            project_dict = {
                "has_auth": getattr(self.project, "has_auth", False),
                "models": getattr(self.project, "models", []),
                "pages": getattr(self.project, "pages", []),
                "all_files": getattr(self.project, "all_files", []),
                "components": getattr(self.project, "components", []),
            }
        
        return {
            "file_type": self.file_type,
            "intent": self.intent,
            "description": self.description,
            "mode": self.mode,
            "complexity": self.complexity,
            "project": project_dict if project_dict else None,
            "has_auth": project_dict.get("has_auth", False),
            "existing_files": project_dict.get("all_files", []),
            "len": len,  # Make len() available
        }


# =============================================================================
# Resolved Config
# =============================================================================

@dataclass
class ResolvedConfig:
    """Configuration resolved for a specific context."""
    system_prompt: str = ""
    suffix_prompt: str = ""
    prompts: List[str] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    patterns: List[Pattern] = field(default_factory=list)
    validation: Optional[ValidationRules] = None
    style: Optional[CodeStyle] = None
    
    def add_prompt(self, prompt: str) -> None:
        """Add a prompt to the list."""
        if prompt and prompt not in self.prompts:
            self.prompts.append(prompt)
    
    def add_rule(self, rule: str) -> None:
        """Add a rule to the list."""
        if rule and rule not in self.rules:
            self.rules.append(rule)
    
    def add_pattern(self, pattern: Pattern) -> None:
        """Add a pattern to the list."""
        if pattern and pattern not in self.patterns:
            self.patterns.append(pattern)
    
    def merge(self, mode_config: ModeConfig) -> None:
        """Merge settings from a mode config."""
        if mode_config.validation:
            self.validation = mode_config.validation
        if mode_config.style:
            self.style = mode_config.style
        if mode_config.prompts:
            if mode_config.prompts.system:
                self.system_prompt = mode_config.prompts.system
            if mode_config.prompts.suffix:
                self.suffix_prompt = mode_config.prompts.suffix
    
    def substitute_vars(self, vars: Dict[str, str]) -> None:
        """Substitute variables in all text fields."""
        for name, value in vars.items():
            pattern = f"${{{name}}}"
            self.system_prompt = self.system_prompt.replace(pattern, str(value))
            self.suffix_prompt = self.suffix_prompt.replace(pattern, str(value))
            self.prompts = [p.replace(pattern, str(value)) for p in self.prompts]
            self.rules = [r.replace(pattern, str(value)) for r in self.rules]
    
    def get_system_prompt(self) -> str:
        """Get the complete system prompt."""
        parts = [self.system_prompt] if self.system_prompt else []
        parts.extend(self.prompts)
        return "\n\n".join(parts)
    
    def get_full_prompt(self, file_type: str = "") -> str:
        """Get the complete prompt including rules."""
        parts = [self.get_system_prompt()]
        
        if self.rules:
            parts.append("## Rules\n" + "\n".join(f"- {r}" for r in self.rules))
        
        if self.patterns:
            parts.append("## Available Patterns")
            for pattern in self.patterns:
                parts.append(f"### {pattern.name}\n{pattern.description}")
        
        if self.suffix_prompt:
            parts.append(self.suffix_prompt)
        
        return "\n\n".join(parts)


# =============================================================================
# Config Resolver
# =============================================================================

class ConfigResolver:
    """Resolves config based on context with priorities."""
    
    def __init__(self, config: PyNextConfig, llm_client: Optional[Any] = None):
        """
        Initialize resolver.
        
        Args:
            config: The PyNext config to resolve
            llm_client: Optional LLM client for evaluating when_llm conditions
        """
        self.config = config
        self.llm = llm_client
        self.vars = self._resolve_variables()
    
    def _resolve_variables(self) -> Dict[str, str]:
        """Get all resolved variables."""
        return dict(self.config.vars)
    
    def _eval_condition(self, when: str, ctx: ConfigContext) -> bool:
        """Evaluate a Python expression condition."""
        if not when:
            return True
        
        try:
            context_dict = ctx.to_dict()
            return eval(when, {"__builtins__": {"len": len}}, context_dict)
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{when}': {e}")
            return False
    
    async def _eval_llm_condition(self, when_llm: str, ctx: ConfigContext) -> bool:
        """Have LLM evaluate a natural language condition."""
        if not when_llm or not self.llm:
            return True if not when_llm else False
        
        prompt = f"""Evaluate if this condition is TRUE or FALSE given the context.
Respond with only "TRUE" or "FALSE".

CONDITION: {when_llm}

CONTEXT:
- File type: {ctx.file_type}
- Intent: {ctx.intent}
- Description: {ctx.description}
- Mode: {ctx.mode}
- Has existing auth: {ctx.project.has_auth if ctx.project else 'unknown'}
- Existing files: {len(ctx.project.all_files) if ctx.project else 0}

Answer:"""

        try:
            response = await self.llm.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}],
            )
            return "TRUE" in response.content[0].text.upper()
        except Exception as e:
            logger.warning(f"Failed to evaluate LLM condition: {e}")
            return False
    
    async def resolve(self, ctx: ConfigContext) -> ResolvedConfig:
        """
        Resolve all config for the given context.
        
        Args:
            ctx: The context to resolve for
            
        Returns:
            Resolved configuration
        """
        resolved = ResolvedConfig()
        
        # Start with base config
        resolved.system_prompt = self.config.prompts.system
        resolved.suffix_prompt = self.config.prompts.suffix
        resolved.validation = self.config.validation
        resolved.style = self.config.style
        
        # Add context prompt
        if self.config.prompts.context:
            resolved.add_prompt(self.config.prompts.context)
        
        # Add always rules
        if self.config.rules.always:
            resolved.add_rule(self.config.rules.always)
        if self.config.rules.custom:
            resolved.add_rule(self.config.rules.custom)
        
        # Apply active mode
        mode_name = ctx.mode or self.config.active_mode
        if mode_name and mode_name in self.config.modes:
            mode_config = self.config.modes[mode_name]
            
            # Handle inheritance
            if mode_config.extends and mode_config.extends in self.config.modes:
                parent = self.config.modes[mode_config.extends]
                resolved.merge(parent)
            
            resolved.merge(mode_config)
        
        # Add file-type specific prompts
        if ctx.file_type:
            type_prompts = self.config.prompts.get_for_type(ctx.file_type)
            if type_prompts.get("prefix"):
                resolved.add_prompt(type_prompts["prefix"])
            if type_prompts.get("suffix"):
                resolved.suffix_prompt = (
                    type_prompts["suffix"] + "\n\n" + resolved.suffix_prompt
                )
        
        # Collect matching conditionals
        candidates = []
        for cond in self.config.conditionals:
            matches = True
            
            # Check Python condition
            if cond.when:
                matches = self._eval_condition(cond.when, ctx)
            
            # Check LLM condition (only if Python passed)
            if matches and cond.when_llm:
                matches = await self._eval_llm_condition(cond.when_llm, ctx)
            
            if matches:
                candidates.append((cond.priority, cond))
        
        # Sort by priority (highest first) and apply
        candidates.sort(key=lambda x: x[0], reverse=True)
        for _, cond in candidates:
            if cond.prompt:
                resolved.add_prompt(self.config.substitute_vars(cond.prompt))
            if cond.rules:
                resolved.add_rule(self.config.substitute_vars(cond.rules))
            if cond.pattern and cond.pattern in self.config.patterns:
                resolved.add_pattern(self.config.patterns[cond.pattern])
        
        # Add matching patterns
        for pattern in self.config.patterns.values():
            if pattern.when:
                if self._eval_condition(pattern.when, ctx):
                    resolved.add_pattern(pattern)
            elif pattern.when_llm:
                if await self._eval_llm_condition(pattern.when_llm, ctx):
                    resolved.add_pattern(pattern)
        
        # Apply variable substitution
        resolved.substitute_vars(self.vars)
        
        return resolved
    
    def resolve_sync(self, ctx: ConfigContext) -> ResolvedConfig:
        """
        Synchronously resolve config (skips LLM conditions).
        
        Args:
            ctx: The context to resolve for
            
        Returns:
            Resolved configuration
        """
        import asyncio
        
        # Create a simple async wrapper that skips LLM
        original_llm = self.llm
        self.llm = None
        
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self.resolve(ctx))
            loop.close()
            return result
        finally:
            self.llm = original_llm


# =============================================================================
# Convenience Functions
# =============================================================================

_config_instance: Optional[PyNextConfig] = None


def get_config(project_path: Optional[Path] = None) -> PyNextConfig:
    """Get or create the config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = PyNextConfig.load(project_path=project_path)
    return _config_instance


def reset_config() -> None:
    """Reset the global config instance."""
    global _config_instance
    _config_instance = None


def validate_config(config_file: Path) -> List[str]:
    """
    Validate a config file.
    
    Args:
        config_file: Path to the config file
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    if not config_file.exists():
        errors.append(f"Config file not found: {config_file}")
        return errors
    
    if tomllib is None:
        errors.append("tomllib not available for validation")
        return errors
    
    try:
        with open(config_file, "rb") as f:
            data = tomllib.load(f)
        
        # Validate AI settings
        if "ai" in data:
            ai = data["ai"]
            if "mode" in ai and ai["mode"] not in ("plan", "agent", "ask"):
                errors.append(f"Invalid ai.mode: {ai['mode']}. Must be plan, agent, or ask.")
        
        # Validate conditionals
        if "conditional" in data:
            for i, cond in enumerate(data["conditional"]):
                if "priority" in cond:
                    if not (0 <= cond["priority"] <= 100):
                        errors.append(f"conditional[{i}].priority must be 0-100")
                
                if "when" in cond:
                    try:
                        compile(cond["when"], "<string>", "eval")
                    except SyntaxError as e:
                        errors.append(f"conditional[{i}].when syntax error: {e}")
        
        # Validate patterns
        if "patterns" in data:
            for name, pattern in data["patterns"].items():
                if "code" in pattern:
                    # Check for unbalanced ${...}
                    code = pattern["code"]
                    opens = code.count("${")
                    closes = code.count("}")
                    if opens > closes:
                        errors.append(f"patterns.{name}.code has unbalanced ${{...}}")
        
        # Validate mode references
        if "mode" in data:
            for mode_name, mode_data in data["mode"].items():
                if "extends" in mode_data:
                    parent = mode_data["extends"]
                    if parent not in data["mode"]:
                        errors.append(
                            f"mode.{mode_name} extends unknown mode: {parent}"
                        )
        
    except Exception as e:
        errors.append(f"Failed to parse config: {e}")
    
    return errors

