"""
PyNext Component Generator.

Generate pages, components, APIs, and more with:
- Interactive prompts (default)
- AI-assisted generation (--ai flag)
- Minimal or full templates (--minimal / --full)

Example:
    # Quick generation
    pynext g page blog
    pynext g component Button
    
    # With AI assistance
    pynext g page products --ai
    
    # Non-interactive
    pynext g api users --yes --minimal
"""

from pynext.generator.core import Generator, GeneratorConfig
from pynext.generator.templates import TEMPLATES, get_template, render_template
from pynext.generator.prompts import prompt_for_type, PROMPTS
from pynext.generator.validators import validate_name, validate_path
from pynext.generator.ai import (
    ai_interview,
    generate_with_ai,
    evaluate_completeness,
    AI_QUESTIONS,
)

__all__ = [
    # Core
    "Generator",
    "GeneratorConfig",
    # Templates
    "TEMPLATES",
    "get_template",
    "render_template",
    # Prompts
    "prompt_for_type",
    "PROMPTS",
    # Validators
    "validate_name",
    "validate_path",
    # AI
    "ai_interview",
    "generate_with_ai",
    "evaluate_completeness",
    "AI_QUESTIONS",
]

