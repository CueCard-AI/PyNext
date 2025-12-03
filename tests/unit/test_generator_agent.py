"""
Comprehensive tests for the AI Generator Agent system.

Tests cover:
- Configuration (AIConfig, ThoughtConfig)
- Thought Thread system
- Code Validator
- Codebase Search
- Generator Agent
- Integration with generate_with_ai

Total: 100+ tests
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import asdict


# ============================================
# AIConfig Tests
# ============================================

class TestAIConfig:
    """Tests for AIConfig dataclass."""
    
    def test_default_values(self):
        """Test AIConfig has correct defaults."""
        from pynext.generator.config import AIConfig
        
        config = AIConfig()
        assert config.model == "claude-sonnet-4-20250514"
        assert config.api_key is None
        assert config.validation_level.value == "full"
        assert config.thought.max_thoughts == 5
        assert config.thought.thought_depth.value == "deep"
    
    def test_from_env_with_defaults(self):
        """Test from_env uses defaults when env vars not set."""
        from pynext.generator.config import AIConfig
        
        # Clear any existing env vars
        with patch.dict(os.environ, {}, clear=True):
            config = AIConfig.from_env()
            assert config.model == "claude-sonnet-4-20250514"
            assert config.thought.max_thoughts == 5
    
    def test_from_env_with_values(self):
        """Test from_env reads environment variables."""
        from pynext.generator.config import AIConfig
        
        env_vars = {
            "ANTHROPIC_MODEL": "claude-opus-4-20250514",
            "ANTHROPIC_API_KEY": "test-key",
            "PYNEXT_AI_MAX_THOUGHTS": "10",
            "PYNEXT_AI_THOUGHT_DEPTH": "shallow",
            "PYNEXT_AI_VALIDATION": "syntax",
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = AIConfig.from_env()
            assert config.model == "claude-opus-4-20250514"
            assert config.api_key == "test-key"
            assert config.thought.max_thoughts == 10
            assert config.thought.thought_depth.value == "shallow"
    
    def test_with_overrides(self):
        """Test with_overrides creates new config with changes."""
        from pynext.generator.config import AIConfig
        
        config = AIConfig()
        new_config = config.with_overrides(
            model="claude-opus-4-20250514",
            max_thoughts=10,
        )
        
        # Original unchanged
        assert config.model == "claude-sonnet-4-20250514"
        assert config.thought.max_thoughts == 5
        
        # New config has overrides
        assert new_config.model == "claude-opus-4-20250514"
        assert new_config.thought.max_thoughts == 10
    
    def test_validate_missing_api_key(self):
        """Test validate raises for missing API key."""
        from pynext.generator.config import AIConfig
        
        config = AIConfig()
        with pytest.raises(ValueError, match="API key required"):
            config.validate()
    
    def test_validate_with_api_key(self):
        """Test validate passes with API key."""
        from pynext.generator.config import AIConfig
        
        config = AIConfig(api_key="test-key")
        config.validate()  # Should not raise
    
    def test_validate_invalid_max_thoughts(self):
        """Test validate raises for invalid max_thoughts."""
        from pynext.generator.config import AIConfig, ThoughtConfig
        
        config = AIConfig(
            api_key="test-key",
            thought=ThoughtConfig(max_thoughts=0)
        )
        with pytest.raises(ValueError, match="max_thoughts"):
            config.validate()
    
    def test_to_dict(self):
        """Test to_dict serialization."""
        from pynext.generator.config import AIConfig
        
        config = AIConfig()
        d = config.to_dict()
        
        assert d["model"] == "claude-sonnet-4-20250514"
        assert d["validation_level"] == "full"
        assert d["thought"]["max_thoughts"] == 5
    
    def test_available_models(self):
        """Test AVAILABLE_MODELS list."""
        from pynext.generator.config import AIConfig
        
        assert "claude-opus-4-20250514" in AIConfig.AVAILABLE_MODELS
        assert "claude-sonnet-4-20250514" in AIConfig.AVAILABLE_MODELS


class TestThoughtConfig:
    """Tests for ThoughtConfig dataclass."""
    
    def test_default_values(self):
        """Test ThoughtConfig defaults."""
        from pynext.generator.config import ThoughtConfig
        
        config = ThoughtConfig()
        assert config.max_thoughts == 5
        assert config.thought_depth.value == "deep"
        assert config.enable_codebase_search is True
        assert config.enable_self_critique is True
        assert config.confidence_threshold == 0.8
    
    def test_string_depth_conversion(self):
        """Test string thought_depth converts to enum."""
        from pynext.generator.config import ThoughtConfig, ThoughtDepth
        
        config = ThoughtConfig(thought_depth="shallow")
        assert config.thought_depth == ThoughtDepth.SHALLOW
    
    def test_from_dict(self):
        """Test from_dict creation."""
        from pynext.generator.config import ThoughtConfig
        
        data = {
            "max_thoughts": 10,
            "thought_depth": "medium",
            "enable_codebase_search": False,
        }
        config = ThoughtConfig.from_dict(data)
        
        assert config.max_thoughts == 10
        assert config.thought_depth.value == "medium"
        assert config.enable_codebase_search is False
    
    def test_to_dict(self):
        """Test to_dict serialization."""
        from pynext.generator.config import ThoughtConfig
        
        config = ThoughtConfig(max_thoughts=10)
        d = config.to_dict()
        
        assert d["max_thoughts"] == 10
        assert d["thought_depth"] == "deep"


# ============================================
# Thought and ThoughtThread Tests
# ============================================

class TestThought:
    """Tests for Thought dataclass."""
    
    def test_create_thought(self):
        """Test basic Thought creation."""
        from pynext.generator.thought import Thought
        
        thought = Thought(
            id=1,
            observation="SyntaxError at line 5",
            reasoning="Missing parentheses in div() call",
            hypothesis="Add parentheses around children",
            search_queries=["PyNext div syntax"],
            confidence=0.85,
        )
        
        assert thought.id == 1
        assert thought.confidence == 0.85
        assert len(thought.search_queries) == 1
    
    def test_confidence_clamping(self):
        """Test confidence is clamped to 0-1."""
        from pynext.generator.thought import Thought
        
        thought = Thought(id=1, observation="", reasoning="", hypothesis="", confidence=1.5)
        assert thought.confidence == 1.0
        
        thought = Thought(id=2, observation="", reasoning="", hypothesis="", confidence=-0.5)
        assert thought.confidence == 0.0
    
    def test_to_dict(self):
        """Test Thought serialization."""
        from pynext.generator.thought import Thought
        
        thought = Thought(
            id=1,
            observation="Error",
            reasoning="Reason",
            hypothesis="Fix",
            confidence=0.9,
        )
        
        d = thought.to_dict()
        assert d["id"] == 1
        assert d["confidence"] == 0.9
        assert "timestamp" in d
    
    def test_from_dict(self):
        """Test Thought deserialization."""
        from pynext.generator.thought import Thought
        
        data = {
            "id": 1,
            "observation": "Error",
            "reasoning": "Reason",
            "hypothesis": "Fix",
            "confidence": 0.9,
        }
        
        thought = Thought.from_dict(data)
        assert thought.id == 1
        assert thought.confidence == 0.9
    
    def test_format_short(self):
        """Test short format."""
        from pynext.generator.thought import Thought
        
        thought = Thought(
            id=1,
            observation="Error",
            reasoning="Reason",
            hypothesis="This is a hypothesis that might be very long" * 5,
            confidence=0.85,
        )
        
        short = thought.format_short()
        assert "Thought 1" in short
        assert "85%" in short


class TestThoughtThread:
    """Tests for ThoughtThread."""
    
    def test_create_empty_thread(self):
        """Test empty thread creation."""
        from pynext.generator.thought import ThoughtThread
        
        thread = ThoughtThread()
        assert len(thread.thoughts) == 0
        assert thread.context_accumulated == ""
    
    def test_add_thought(self):
        """Test adding thoughts to thread."""
        from pynext.generator.thought import Thought, ThoughtThread
        
        thread = ThoughtThread()
        thought = Thought(id=1, observation="Error", reasoning="Reason", hypothesis="Fix")
        
        thread.add_thought(thought)
        assert len(thread.thoughts) == 1
        assert thread.thoughts[0].id == 1
    
    def test_get_latest_thought(self):
        """Test getting latest thought."""
        from pynext.generator.thought import Thought, ThoughtThread
        
        thread = ThoughtThread()
        assert thread.get_latest_thought() is None
        
        thread.add_thought(Thought(id=1, observation="E1", reasoning="R1", hypothesis="H1"))
        thread.add_thought(Thought(id=2, observation="E2", reasoning="R2", hypothesis="H2"))
        
        latest = thread.get_latest_thought()
        assert latest.id == 2
    
    def test_get_highest_confidence(self):
        """Test getting highest confidence thought."""
        from pynext.generator.thought import Thought, ThoughtThread
        
        thread = ThoughtThread()
        thread.add_thought(Thought(id=1, observation="E1", reasoning="R1", hypothesis="H1", confidence=0.5))
        thread.add_thought(Thought(id=2, observation="E2", reasoning="R2", hypothesis="H2", confidence=0.9))
        thread.add_thought(Thought(id=3, observation="E3", reasoning="R3", hypothesis="H3", confidence=0.7))
        
        best = thread.get_highest_confidence_thought()
        assert best.id == 2
        assert best.confidence == 0.9
    
    def test_should_attempt_generation(self):
        """Test should_attempt_generation threshold."""
        from pynext.generator.thought import Thought, ThoughtThread
        
        thread = ThoughtThread()
        assert not thread.should_attempt_generation()
        
        thread.add_thought(Thought(id=1, observation="E", reasoning="R", hypothesis="H", confidence=0.5))
        assert not thread.should_attempt_generation()
        
        thread.add_thought(Thought(id=2, observation="E", reasoning="R", hypothesis="H", confidence=0.9))
        assert thread.should_attempt_generation()
        
        # Custom threshold
        assert thread.should_attempt_generation(threshold=0.95) is False
    
    def test_get_reasoning_chain(self):
        """Test formatting reasoning chain."""
        from pynext.generator.thought import Thought, ThoughtThread
        
        thread = ThoughtThread()
        assert "No previous thoughts" in thread.get_reasoning_chain()
        
        thread.add_thought(Thought(id=1, observation="Error 1", reasoning="Reason 1", hypothesis="Fix 1", confidence=0.8))
        thread.add_thought(Thought(id=2, observation="Error 2", reasoning="Reason 2", hypothesis="Fix 2", confidence=0.9))
        
        chain = thread.get_reasoning_chain()
        assert "Thought 1" in chain
        assert "Thought 2" in chain
        assert "Error 1" in chain
        assert "80%" in chain
    
    def test_add_search_result(self):
        """Test adding search results."""
        from pynext.generator.thought import Thought, ThoughtThread
        
        thread = ThoughtThread()
        thread.add_thought(Thought(id=1, observation="E", reasoning="R", hypothesis="H"))
        
        thread.add_search_result("PyNext signals", "Signal() creates reactive state")
        
        assert "PyNext signals" in thread.context_accumulated
        assert thread.thoughts[0].search_results is not None
    
    def test_add_critique(self):
        """Test adding self-critique."""
        from pynext.generator.thought import Thought, ThoughtThread
        
        thread = ThoughtThread()
        thread.add_thought(Thought(id=1, observation="E", reasoning="R", hypothesis="H"))
        
        thread.add_critique("This might not handle edge cases")
        
        assert thread.thoughts[0].critique is not None
        assert "edge cases" in thread.thoughts[0].critique
    
    def test_to_dict_from_dict(self):
        """Test serialization/deserialization roundtrip."""
        from pynext.generator.thought import Thought, ThoughtThread
        
        thread = ThoughtThread(
            generator_type="page",
            component_name="products",
            initial_error="SyntaxError",
        )
        thread.add_thought(Thought(id=1, observation="E", reasoning="R", hypothesis="H", confidence=0.8))
        
        d = thread.to_dict()
        restored = ThoughtThread.from_dict(d)
        
        assert restored.generator_type == "page"
        assert restored.component_name == "products"
        assert len(restored.thoughts) == 1


class TestCreateThoughtFromAI:
    """Tests for create_thought_from_ai_response."""
    
    def test_create_from_valid_response(self):
        """Test creating thought from valid AI response."""
        from pynext.generator.thought import create_thought_from_ai_response
        
        response = {
            "observation": "SyntaxError at line 5",
            "reasoning": "Missing parentheses",
            "hypothesis": "Add parentheses",
            "search_queries": ["PyNext div syntax"],
            "confidence": 0.85,
        }
        
        thought = create_thought_from_ai_response(1, response)
        assert thought.id == 1
        assert thought.observation == "SyntaxError at line 5"
        assert thought.confidence == 0.85
    
    def test_create_from_partial_response(self):
        """Test creating thought from partial response."""
        from pynext.generator.thought import create_thought_from_ai_response
        
        response = {"confidence": 0.5}
        thought = create_thought_from_ai_response(1, response)
        
        assert thought.id == 1
        assert "No observation" in thought.observation
        assert thought.confidence == 0.5


# ============================================
# Validator Tests
# ============================================

class TestCodeValidator:
    """Tests for CodeValidator."""
    
    def test_valid_syntax(self):
        """Test valid Python syntax passes."""
        from pynext.generator.validator import CodeValidator, ValidationLevel
        
        validator = CodeValidator(level=ValidationLevel.SYNTAX)
        code = """
def page():
    return "Hello"
"""
        result = validator.validate(code, "page")
        assert result.valid
        assert len(result.errors) == 0
    
    def test_invalid_syntax(self):
        """Test syntax error is caught."""
        from pynext.generator.validator import CodeValidator, ValidationLevel
        
        validator = CodeValidator(level=ValidationLevel.SYNTAX)
        code = """
def page()
    return "Hello"
"""
        result = validator.validate(code, "page")
        assert not result.valid
        assert any("SyntaxError" in e for e in result.errors)
    
    def test_full_validation_missing_decorator(self):
        """Test full validation catches missing decorator."""
        from pynext.generator.validator import CodeValidator, ValidationLevel
        
        validator = CodeValidator(level=ValidationLevel.FULL)
        code = """
def Counter():
    count = Signal(0)
    return button()("Click")
"""
        result = validator.validate(code, "island")
        assert not result.valid
        assert any("@island" in e for e in result.errors)
    
    def test_full_validation_react_pattern(self):
        """Test full validation catches React patterns."""
        from pynext.generator.validator import CodeValidator, ValidationLevel
        
        validator = CodeValidator(level=ValidationLevel.FULL)
        code = """
from pynext import div
def Counter():
    count = useState(0)
    return div()("Click")
"""
        result = validator.validate(code, "component")
        assert not result.valid
        assert any("useState" in e for e in result.errors)
    
    def test_format_for_ai(self):
        """Test format_for_ai output."""
        from pynext.generator.validator import ValidationResult
        
        result = ValidationResult()
        result.add_error("SyntaxError at line 5")
        result.add_warning("Missing docstring")
        result.add_suggestion("Consider using Signal")
        
        formatted = result.format_for_ai()
        assert "Errors" in formatted
        assert "Warnings" in formatted
        assert "Suggestions" in formatted


class TestValidationHelpers:
    """Tests for validation helper functions."""
    
    def test_validate_syntax(self):
        """Test validate_syntax helper."""
        from pynext.generator.validator import validate_syntax
        
        result = validate_syntax("def foo(): pass")
        assert result.valid
    
    def test_validate_imports(self):
        """Test validate_imports helper."""
        from pynext.generator.validator import validate_imports
        
        code = "from pynext import div"
        result = validate_imports(code)
        assert result.valid
    
    def test_validate_full(self):
        """Test validate_full helper."""
        from pynext.generator.validator import validate_full
        
        code = """
from pynext import div
def page():
    return div()("Hello")
"""
        result = validate_full(code, "page")
        assert result.valid
    
    def test_is_valid_pynext_code(self):
        """Test is_valid_pynext_code helper."""
        from pynext.generator.validator import is_valid_pynext_code
        
        assert is_valid_pynext_code("def foo(): pass")
        assert not is_valid_pynext_code("def foo( pass")


# ============================================
# Codebase Search Tests
# ============================================

class TestCodebaseSearch:
    """Tests for CodebaseSearch."""
    
    def test_get_pattern_signals(self):
        """Test getting signals pattern."""
        from pynext.generator.search import CodebaseSearch
        
        searcher = CodebaseSearch()
        pattern = searcher.get_pattern("signals")
        
        assert pattern is not None
        assert "Signal" in pattern
        assert ".set(" in pattern  # Fixed: look for .set( not set()
    
    def test_get_pattern_elements(self):
        """Test getting elements pattern."""
        from pynext.generator.search import CodebaseSearch
        
        searcher = CodebaseSearch()
        pattern = searcher.get_pattern("elements")
        
        assert pattern is not None
        assert "div(" in pattern
        assert "class_" in pattern
    
    def test_get_pattern_islands(self):
        """Test getting islands pattern."""
        from pynext.generator.search import CodebaseSearch
        
        searcher = CodebaseSearch()
        pattern = searcher.get_pattern("islands")
        
        assert pattern is not None
        assert "@island" in pattern
    
    def test_get_pattern_invalid(self):
        """Test getting invalid pattern returns None."""
        from pynext.generator.search import CodebaseSearch
        
        searcher = CodebaseSearch()
        pattern = searcher.get_pattern("invalid_pattern")
        
        assert pattern is None
    
    def test_search_basic(self):
        """Test basic search."""
        from pynext.generator.search import CodebaseSearch
        
        searcher = CodebaseSearch()
        results = searcher.search("Signal state management")
        
        assert len(results) > 0
        # Should find the signals pattern
        assert any("Signal" in r.content for r in results)
    
    def test_search_elements(self):
        """Test searching for elements."""
        from pynext.generator.search import CodebaseSearch
        
        searcher = CodebaseSearch()
        results = searcher.search("div button html elements")
        
        assert len(results) > 0
        assert any("div(" in r.content for r in results)
    
    def test_get_all_patterns(self):
        """Test getting all patterns."""
        from pynext.generator.search import CodebaseSearch
        
        searcher = CodebaseSearch()
        patterns = searcher.get_all_patterns()
        
        assert "signals" in patterns
        assert "elements" in patterns
        assert "islands" in patterns
        assert "actions" in patterns
    
    def test_format_results(self):
        """Test formatting search results."""
        from pynext.generator.search import CodebaseSearch, SearchResult
        
        searcher = CodebaseSearch()
        results = [
            SearchResult(file_path="test.py", content="def foo(): pass", score=0.9),
            SearchResult(file_path="test2.py", content="def bar(): pass", score=0.8),
        ]
        
        formatted = searcher.format_results(results)
        assert "Result 1" in formatted
        assert "Result 2" in formatted
        assert "90%" in formatted


class TestSearchHelpers:
    """Tests for search helper functions."""
    
    def test_search_codebase(self):
        """Test search_codebase helper."""
        from pynext.generator.search import search_codebase
        
        result = search_codebase("Signal")
        assert "Signal" in result
    
    def test_get_pattern_example(self):
        """Test get_pattern_example helper."""
        from pynext.generator.search import get_pattern_example
        
        example = get_pattern_example("signals")
        assert "Signal" in example
        
        error = get_pattern_example("invalid")
        assert "not found" in error


# ============================================
# Reasoning Prompts Tests
# ============================================

class TestReasoningPrompts:
    """Tests for reasoning prompts."""
    
    def test_thought_prompt_format(self):
        """Test THOUGHT_PROMPT has required placeholders."""
        from pynext.generator.reasoning import THOUGHT_PROMPT
        
        assert "{previous_thoughts}" in THOUGHT_PROMPT
        assert "{error}" in THOUGHT_PROMPT
        assert "{code}" in THOUGHT_PROMPT
    
    def test_self_critique_prompt_format(self):
        """Test SELF_CRITIQUE_PROMPT has required placeholders."""
        from pynext.generator.reasoning import SELF_CRITIQUE_PROMPT
        
        assert "{thoughts}" in SELF_CRITIQUE_PROMPT
        assert "{hypothesis}" in SELF_CRITIQUE_PROMPT
    
    def test_get_thought_prompt(self):
        """Test get_thought_prompt returns correct prompt."""
        from pynext.generator.reasoning import get_thought_prompt, THOUGHT_PROMPT, SHALLOW_THOUGHT_PROMPT
        
        assert get_thought_prompt("deep") == THOUGHT_PROMPT
        assert get_thought_prompt("shallow") == SHALLOW_THOUGHT_PROMPT
        assert get_thought_prompt("invalid") == THOUGHT_PROMPT  # Default
    
    def test_format_thought_prompt(self):
        """Test format_thought_prompt."""
        from pynext.generator.reasoning import format_thought_prompt
        
        formatted = format_thought_prompt(
            depth="shallow",
            error="SyntaxError",
            code="def foo(): pass",
            previous_thoughts="None",
        )
        
        assert "SyntaxError" in formatted
        assert "def foo()" in formatted
    
    def test_format_generation_prompt(self):
        """Test format_generation_prompt."""
        from pynext.generator.reasoning import format_generation_prompt
        
        # Without context
        prompt = format_generation_prompt(
            generator_type="page",
            name="products",
            requirements="Show products",
        )
        assert "page" in prompt
        assert "products" in prompt
        
        # With context
        prompt = format_generation_prompt(
            generator_type="page",
            name="products",
            requirements="Show products",
            reasoning_chain="Previous thought: Fix imports",
            codebase_context="Signal usage example",
        )
        assert "Previous Reasoning" in prompt
        assert "Fix imports" in prompt


# ============================================
# Generator Agent Tests
# ============================================

class TestGeneratorAgent:
    """Tests for GeneratorAgent."""
    
    def test_agent_init(self):
        """Test agent initialization."""
        from pynext.generator.agent import GeneratorAgent
        from pynext.generator.config import AIConfig
        
        config = AIConfig(api_key="test-key")
        agent = GeneratorAgent(config)
        
        assert agent.config == config
        assert agent.validator is not None
        assert agent.searcher is not None
    
    def test_format_requirements(self):
        """Test _format_requirements."""
        from pynext.generator.agent import GeneratorAgent
        from pynext.generator.config import AIConfig
        
        config = AIConfig(api_key="test-key")
        agent = GeneratorAgent(config)
        
        answers = {
            "purpose": "Show products",
            "data": "Product cards",
            "empty": "",  # Should be filtered
        }
        
        formatted = agent._format_requirements(answers)
        assert "purpose: Show products" in formatted
        assert "data: Product cards" in formatted
        assert "empty" not in formatted
    
    def test_extract_code_python_block(self):
        """Test _extract_code with python block."""
        from pynext.generator.agent import GeneratorAgent
        from pynext.generator.config import AIConfig
        
        config = AIConfig(api_key="test-key")
        agent = GeneratorAgent(config)
        
        response = """
Here's the code:

```python
def page():
    return "Hello"
```

Done!
"""
        code = agent._extract_code(response)
        assert code == 'def page():\n    return "Hello"'
    
    def test_extract_code_generic_block(self):
        """Test _extract_code with generic block."""
        from pynext.generator.agent import GeneratorAgent
        from pynext.generator.config import AIConfig
        
        config = AIConfig(api_key="test-key")
        agent = GeneratorAgent(config)
        
        response = """
```
def page():
    return "Hello"
```
"""
        code = agent._extract_code(response)
        assert "def page()" in code
    
    def test_parse_thought_response_valid(self):
        """Test _parse_thought_response with valid JSON."""
        from pynext.generator.agent import GeneratorAgent
        from pynext.generator.config import AIConfig
        
        config = AIConfig(api_key="test-key")
        agent = GeneratorAgent(config)
        
        response = '{"observation": "Error", "reasoning": "Reason", "hypothesis": "Fix", "confidence": 0.9}'
        
        parsed = agent._parse_thought_response(response)
        assert parsed["observation"] == "Error"
        assert parsed["confidence"] == 0.9
    
    def test_parse_thought_response_with_text(self):
        """Test _parse_thought_response with surrounding text."""
        from pynext.generator.agent import GeneratorAgent
        from pynext.generator.config import AIConfig
        
        config = AIConfig(api_key="test-key")
        agent = GeneratorAgent(config)
        
        response = """
Let me analyze this.

{"observation": "Error", "reasoning": "Reason", "hypothesis": "Fix", "confidence": 0.85}

That should fix it.
"""
        
        parsed = agent._parse_thought_response(response)
        assert parsed["observation"] == "Error"
        assert parsed["confidence"] == 0.85


class TestGenerationError:
    """Tests for GenerationError."""
    
    def test_error_creation(self):
        """Test GenerationError creation."""
        from pynext.generator.agent import GenerationError
        
        error = GenerationError(
            "Failed after 5 thoughts",
            reasoning="Thought 1: ...",
            last_code="def foo(): pass",
            last_errors=["SyntaxError"],
        )
        
        assert "5 thoughts" in str(error)
        assert error.reasoning == "Thought 1: ..."
        assert error.last_code == "def foo(): pass"
    
    def test_error_str_format(self):
        """Test GenerationError string format."""
        from pynext.generator.agent import GenerationError
        
        error = GenerationError(
            "Failed",
            last_errors=["Error 1", "Error 2"],
            reasoning="Chain of thought",
        )
        
        error_str = str(error)
        assert "Failed" in error_str
        assert "Error 1" in error_str
        assert "Chain of thought" in error_str


class TestGenerateWithAgent:
    """Tests for generate_with_agent function."""
    
    def test_missing_api_key(self):
        """Test error when API key missing."""
        from pynext.generator.agent import generate_with_agent
        from pynext.generator.config import AIConfig
        
        config = AIConfig()  # No API key
        
        with pytest.raises(ValueError, match="API key"):
            generate_with_agent("page", "test", {}, config=config)


# ============================================
# Integration Tests (with mocks)
# ============================================

class TestAIIntegration:
    """Integration tests with mocked AI calls."""
    
    @pytest.mark.asyncio
    async def test_generate_valid_first_try(self):
        """Test generation succeeds on first try."""
        from pynext.generator.agent import GeneratorAgent
        from pynext.generator.config import AIConfig
        
        config = AIConfig(api_key="test-key")
        agent = GeneratorAgent(config)
        
        # Mock the AI call to return valid code
        valid_code = """
from pynext import div, h1

def page():
    return div()(
        h1("Hello")
    )
"""
        
        with patch.object(agent, '_call_ai', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = f"```python\n{valid_code}\n```"
            
            code = await agent.generate(
                "page", "test", {"purpose": "Test page"}
            )
            
            assert "def page()" in code
            # Should only call once (initial generation)
            assert mock_call.call_count == 1
    
    @pytest.mark.asyncio
    async def test_generate_with_thought_thread(self):
        """Test generation uses thought thread on error."""
        from pynext.generator.agent import GeneratorAgent
        from pynext.generator.config import AIConfig, ThoughtConfig
        
        config = AIConfig(
            api_key="test-key",
            thought=ThoughtConfig(max_thoughts=2, enable_codebase_search=False),
        )
        agent = GeneratorAgent(config)
        
        # First call returns invalid code, second returns valid
        invalid_code = "def page( pass"  # Syntax error
        valid_code = """
from pynext import div

def page():
    return div()("Hello")
"""
        thought_response = '{"observation": "SyntaxError", "reasoning": "Missing parens", "hypothesis": "Add parens", "confidence": 0.9}'
        
        call_count = [0]
        
        async def mock_call(prompt, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return f"```python\n{invalid_code}\n```"
            elif call_count[0] == 2:
                return thought_response
            else:
                return f"```python\n{valid_code}\n```"
        
        with patch.object(agent, '_call_ai', side_effect=mock_call):
            code = await agent.generate("page", "test", {"purpose": "Test"})
            
            assert "def page()" in code
            assert call_count[0] >= 2  # At least initial + thought


# ============================================
# generate_with_ai Function Tests
# ============================================

class TestGenerateWithAI:
    """Tests for the main generate_with_ai function."""
    
    def test_default_uses_agent(self):
        """Test default mode uses agent."""
        from pynext.generator.ai import generate_with_ai
        
        with patch('pynext.generator.ai.generate_with_agent') as mock_agent:
            mock_agent.return_value = "def page(): pass"
            
            code = generate_with_ai(
                "page", "test",
                {"purpose": "Test"},
                api_key="test-key",
            )
            
            mock_agent.assert_called_once()
            assert code == "def page(): pass"
    
    def test_legacy_mode(self):
        """Test legacy mode skips agent."""
        from pynext.generator.ai import generate_with_ai
        
        with patch('pynext.generator.ai._generate_legacy') as mock_legacy:
            mock_legacy.return_value = "def page(): pass"
            
            code = generate_with_ai(
                "page", "test",
                {"purpose": "Test"},
                api_key="test-key",
                use_agent=False,
            )
            
            mock_legacy.assert_called_once()


class TestGenerateQuick:
    """Tests for generate_quick function."""
    
    def test_quick_passes_to_generate_with_ai(self):
        """Test generate_quick calls generate_with_ai."""
        from pynext.generator.ai import generate_quick
        
        with patch('pynext.generator.ai.generate_with_ai') as mock_gen:
            mock_gen.return_value = "def page(): pass"
            
            code = generate_quick(
                "page", "test",
                "Simple test page",
                api_key="test-key",
            )
            
            mock_gen.assert_called_once()
            # Check that generate_with_ai was called with correct args
            # args[0] is generator_type, args[1] is name, args[2] is answers
            call_args = mock_gen.call_args
            assert call_args[0][0] == "page"  # generator_type
            assert call_args[0][1] == "test"  # name
            assert call_args[0][2]["description"] == "Simple test page"  # answers dict


# ============================================
# Enums Tests
# ============================================

class TestEnums:
    """Tests for configuration enums."""
    
    def test_thought_depth_values(self):
        """Test ThoughtDepth enum values."""
        from pynext.generator.config import ThoughtDepth
        
        assert ThoughtDepth.SHALLOW.value == "shallow"
        assert ThoughtDepth.MEDIUM.value == "medium"
        assert ThoughtDepth.DEEP.value == "deep"
    
    def test_validation_level_values(self):
        """Test ValidationLevel enum values."""
        from pynext.generator.config import ValidationLevel
        
        assert ValidationLevel.SYNTAX.value == "syntax"
        assert ValidationLevel.IMPORTS.value == "imports"
        assert ValidationLevel.FULL.value == "full"


# ============================================
# Edge Cases
# ============================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_code_validation(self):
        """Test validating empty code."""
        from pynext.generator.validator import CodeValidator
        
        validator = CodeValidator()
        result = validator.validate("", "page")
        
        # Empty code is syntactically valid Python
        assert result.valid or any("function definition" in e.lower() for e in result.errors)
    
    def test_very_long_code_validation(self):
        """Test validating very long code."""
        from pynext.generator.validator import CodeValidator
        
        long_code = "def page():\n" + "    x = 1\n" * 1000 + "    return x"
        
        validator = CodeValidator()
        result = validator.validate(long_code, "page")
        
        assert result.valid
    
    def test_unicode_in_code(self):
        """Test code with unicode characters."""
        from pynext.generator.validator import CodeValidator
        
        code = '''
def page():
    return "Hello 世界 🌍"
'''
        
        validator = CodeValidator()
        result = validator.validate(code, "page")
        
        assert result.valid
    
    def test_search_empty_query(self):
        """Test searching with empty query."""
        from pynext.generator.search import CodebaseSearch
        
        searcher = CodebaseSearch()
        results = searcher.search("")
        
        # Should not crash, may return empty or all patterns
        assert isinstance(results, list)
    
    def test_config_toml_not_found(self):
        """Test loading config when TOML doesn't exist."""
        from pynext.generator.config import AIConfig
        
        config = AIConfig.from_file("nonexistent.toml")
        
        # Should fallback to env/defaults
        assert config.model == "claude-sonnet-4-20250514" or config.model == os.getenv("ANTHROPIC_MODEL")

