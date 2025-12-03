"""
AI Generator Configuration.

Provides configurable settings for the AI code generation system including:
- Model selection (CLI > env > config > default)
- Thought thread configuration (max thoughts, depth, features)
- Validation levels

Example:
    # Default config from environment
    config = AIConfig.from_env()
    
    # Override specific settings
    config = AIConfig(
        model="claude-opus-4-20250514",
        thought=ThoughtConfig(max_thoughts=10, thought_depth="deep")
    )
    
    # From TOML config file
    config = AIConfig.from_file("pynext.ai.toml")
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python
    except ImportError:
        tomllib = None  # type: ignore


# ============================================
# Enums
# ============================================

class ThoughtDepth(str, Enum):
    """
    How deep the AI should think about errors.
    
    - SHALLOW: Fast, 1-2 thoughts. Just identify error and suggest fix.
    - MEDIUM: Balanced, 2-3 thoughts. Analyze root cause.
    - DEEP: Thorough, 3-5 thoughts. Full analysis with self-critique.
    """
    SHALLOW = "shallow"
    MEDIUM = "medium"
    DEEP = "deep"


class ValidationLevel(str, Enum):
    """
    How thoroughly to validate generated code.
    
    - SYNTAX: Just compile() check - fast but minimal.
    - IMPORTS: Syntax + verify imports are valid PyNext modules.
    - FULL: Syntax + imports + PyNext patterns (signals, elements, decorators).
    """
    SYNTAX = "syntax"
    IMPORTS = "imports"
    FULL = "full"


# ============================================
# Thought Configuration
# ============================================

@dataclass
class ThoughtConfig:
    """
    Configuration for the thought thread reasoning system.
    
    The thought thread is a chain-of-thought reasoning system where each
    step builds on the previous, allowing the AI to deeply analyze mistakes
    rather than blindly retrying.
    
    Attributes:
        max_thoughts: Maximum number of reasoning steps (default: 5)
        thought_depth: How deep to analyze - shallow/medium/deep (default: deep)
        enable_codebase_search: Allow AI to search PyNext docs/code (default: True)
        enable_self_critique: AI reviews its own solutions (default: True)
        require_explanation: AI must explain reasoning (default: True)
        confidence_threshold: Minimum confidence to attempt generation (default: 0.8)
    
    Example:
        # Quick generation with minimal thinking
        config = ThoughtConfig(max_thoughts=2, thought_depth=ThoughtDepth.SHALLOW)
        
        # Thorough analysis for complex components
        config = ThoughtConfig(
            max_thoughts=10,
            thought_depth=ThoughtDepth.DEEP,
            enable_self_critique=True
        )
    """
    max_thoughts: int = 5
    thought_depth: ThoughtDepth = ThoughtDepth.DEEP
    enable_codebase_search: bool = True
    enable_self_critique: bool = True
    require_explanation: bool = True
    confidence_threshold: float = 0.8
    
    def __post_init__(self) -> None:
        """Convert string values to enums if needed."""
        if isinstance(self.thought_depth, str):
            self.thought_depth = ThoughtDepth(self.thought_depth)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThoughtConfig":
        """Create ThoughtConfig from dictionary."""
        return cls(
            max_thoughts=data.get("max_thoughts", 5),
            thought_depth=data.get("thought_depth", "deep"),
            enable_codebase_search=data.get("enable_codebase_search", True),
            enable_self_critique=data.get("enable_self_critique", True),
            require_explanation=data.get("require_explanation", True),
            confidence_threshold=data.get("confidence_threshold", 0.8),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "max_thoughts": self.max_thoughts,
            "thought_depth": self.thought_depth.value if isinstance(self.thought_depth, ThoughtDepth) else self.thought_depth,
            "enable_codebase_search": self.enable_codebase_search,
            "enable_self_critique": self.enable_self_critique,
            "require_explanation": self.require_explanation,
            "confidence_threshold": self.confidence_threshold,
        }


# ============================================
# AI Configuration
# ============================================

@dataclass
class AIConfig:
    """
    Main configuration for AI code generation.
    
    Configuration Priority (highest to lowest):
    1. Function parameter (model=, max_thoughts=)
    2. Environment variable (ANTHROPIC_MODEL, PYNEXT_AI_MAX_THOUGHTS)
    3. Config file (pynext.ai.toml)
    4. Default values
    
    Attributes:
        model: Anthropic model to use (default: claude-sonnet-4-20250514)
        api_key: Anthropic API key (default: from ANTHROPIC_API_KEY env)
        validation_level: How thoroughly to validate - syntax/imports/full
        thought: ThoughtConfig for reasoning settings
    
    Example:
        # Load from environment with defaults
        config = AIConfig.from_env()
        
        # Explicit configuration
        config = AIConfig(
            model="claude-opus-4-20250514",
            validation_level=ValidationLevel.FULL,
            thought=ThoughtConfig(max_thoughts=10)
        )
        
        # Override specific settings
        config = config.with_overrides(model="claude-sonnet-4-20250514")
    """
    model: str = "claude-sonnet-4-20250514"
    api_key: Optional[str] = None
    validation_level: ValidationLevel = ValidationLevel.FULL
    thought: ThoughtConfig = field(default_factory=ThoughtConfig)
    
    # Default models for reference
    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    AVAILABLE_MODELS = [
        "claude-opus-4-20250514",
        "claude-sonnet-4-20250514",
        "claude-haiku-3-20240307",
    ]
    
    def __post_init__(self) -> None:
        """Convert string values to enums if needed."""
        if isinstance(self.validation_level, str):
            self.validation_level = ValidationLevel(self.validation_level)
    
    @classmethod
    def from_env(cls) -> "AIConfig":
        """
        Create AIConfig from environment variables.
        
        Environment variables:
        - ANTHROPIC_API_KEY: API key for Anthropic
        - ANTHROPIC_MODEL: Model to use
        - PYNEXT_AI_MAX_THOUGHTS: Max reasoning steps
        - PYNEXT_AI_THOUGHT_DEPTH: shallow/medium/deep
        - PYNEXT_AI_VALIDATION: syntax/imports/full
        - PYNEXT_AI_CODEBASE_SEARCH: true/false
        - PYNEXT_AI_SELF_CRITIQUE: true/false
        - PYNEXT_AI_CONFIDENCE_THRESHOLD: 0.0-1.0
        
        Returns:
            AIConfig with values from environment
        """
        thought_config = ThoughtConfig(
            max_thoughts=int(os.getenv("PYNEXT_AI_MAX_THOUGHTS", "5")),
            thought_depth=os.getenv("PYNEXT_AI_THOUGHT_DEPTH", "deep"),
            enable_codebase_search=os.getenv("PYNEXT_AI_CODEBASE_SEARCH", "true").lower() == "true",
            enable_self_critique=os.getenv("PYNEXT_AI_SELF_CRITIQUE", "true").lower() == "true",
            confidence_threshold=float(os.getenv("PYNEXT_AI_CONFIDENCE_THRESHOLD", "0.8")),
        )
        
        return cls(
            model=os.getenv("ANTHROPIC_MODEL", cls.DEFAULT_MODEL),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            validation_level=os.getenv("PYNEXT_AI_VALIDATION", "full"),
            thought=thought_config,
        )
    
    @classmethod
    def from_file(cls, path: str = "pynext.ai.toml") -> "AIConfig":
        """
        Load AIConfig from TOML file.
        
        Expected format:
        ```toml
        [ai]
        model = "claude-sonnet-4-20250514"
        validation_level = "full"
        
        [ai.thought]
        max_thoughts = 5
        thought_depth = "deep"
        enable_codebase_search = true
        enable_self_critique = true
        ```
        
        Args:
            path: Path to TOML config file
        
        Returns:
            AIConfig from file, or default if file not found
        """
        if tomllib is None:
            return cls.from_env()
        
        config_path = Path(path)
        if not config_path.exists():
            return cls.from_env()
        
        try:
            with open(config_path, "rb") as f:
                data = tomllib.load(f)
            
            ai_data = data.get("ai", {})
            thought_data = ai_data.get("thought", {})
            
            thought_config = ThoughtConfig.from_dict(thought_data)
            
            return cls(
                model=ai_data.get("model", cls.DEFAULT_MODEL),
                api_key=ai_data.get("api_key") or os.getenv("ANTHROPIC_API_KEY"),
                validation_level=ai_data.get("validation_level", "full"),
                thought=thought_config,
            )
        except Exception:
            return cls.from_env()
    
    @classmethod
    def load(cls) -> "AIConfig":
        """
        Load configuration with full priority chain.
        
        Priority: Config file < Environment variables
        (CLI overrides are applied later via with_overrides)
        
        Returns:
            AIConfig with merged settings
        """
        # Start with file config (if exists)
        config = cls.from_file()
        
        # Override with environment variables where set
        env_config = cls.from_env()
        
        if os.getenv("ANTHROPIC_MODEL"):
            config.model = env_config.model
        if os.getenv("ANTHROPIC_API_KEY"):
            config.api_key = env_config.api_key
        if os.getenv("PYNEXT_AI_VALIDATION"):
            config.validation_level = env_config.validation_level
        if os.getenv("PYNEXT_AI_MAX_THOUGHTS"):
            config.thought.max_thoughts = env_config.thought.max_thoughts
        if os.getenv("PYNEXT_AI_THOUGHT_DEPTH"):
            config.thought.thought_depth = env_config.thought.thought_depth
        if os.getenv("PYNEXT_AI_CODEBASE_SEARCH"):
            config.thought.enable_codebase_search = env_config.thought.enable_codebase_search
        if os.getenv("PYNEXT_AI_SELF_CRITIQUE"):
            config.thought.enable_self_critique = env_config.thought.enable_self_critique
        if os.getenv("PYNEXT_AI_CONFIDENCE_THRESHOLD"):
            config.thought.confidence_threshold = env_config.thought.confidence_threshold
        
        return config
    
    def with_overrides(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        validation_level: Optional[str] = None,
        max_thoughts: Optional[int] = None,
        thought_depth: Optional[str] = None,
        enable_codebase_search: Optional[bool] = None,
        enable_self_critique: Optional[bool] = None,
        confidence_threshold: Optional[float] = None,
    ) -> "AIConfig":
        """
        Create new config with CLI/function overrides applied.
        
        This is the highest priority - overrides environment and file settings.
        
        Args:
            model: Override model
            api_key: Override API key
            validation_level: Override validation level
            max_thoughts: Override max thoughts
            thought_depth: Override thought depth
            enable_codebase_search: Override codebase search
            enable_self_critique: Override self critique
            confidence_threshold: Override confidence threshold
        
        Returns:
            New AIConfig with overrides applied
        """
        new_thought = ThoughtConfig(
            max_thoughts=max_thoughts if max_thoughts is not None else self.thought.max_thoughts,
            thought_depth=thought_depth if thought_depth is not None else self.thought.thought_depth,
            enable_codebase_search=enable_codebase_search if enable_codebase_search is not None else self.thought.enable_codebase_search,
            enable_self_critique=enable_self_critique if enable_self_critique is not None else self.thought.enable_self_critique,
            require_explanation=self.thought.require_explanation,
            confidence_threshold=confidence_threshold if confidence_threshold is not None else self.thought.confidence_threshold,
        )
        
        return AIConfig(
            model=model if model is not None else self.model,
            api_key=api_key if api_key is not None else self.api_key,
            validation_level=validation_level if validation_level is not None else self.validation_level,
            thought=new_thought,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "model": self.model,
            "validation_level": self.validation_level.value if isinstance(self.validation_level, ValidationLevel) else self.validation_level,
            "thought": self.thought.to_dict(),
        }
    
    def validate(self) -> None:
        """
        Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required.\n"
                "Set ANTHROPIC_API_KEY environment variable or pass --api-key"
            )
        
        if self.thought.max_thoughts < 1:
            raise ValueError("max_thoughts must be at least 1")
        
        if not 0.0 <= self.thought.confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")


# ============================================
# Helper Functions
# ============================================

def get_default_config() -> AIConfig:
    """Get default AI configuration."""
    return AIConfig.load()


def get_model_from_env() -> str:
    """Get model from environment or return default."""
    return os.getenv("ANTHROPIC_MODEL", AIConfig.DEFAULT_MODEL)

