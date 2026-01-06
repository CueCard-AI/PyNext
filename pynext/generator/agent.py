"""
Generator Agent with Thought Thread Reasoning.

The GeneratorAgent orchestrates the AI code generation process with
a chain-of-thought reasoning system. Instead of blindly retrying on errors,
it thinks deeply about what went wrong and why.

Process:
1. Generate initial code
2. Validate the code
3. If invalid: Think about the error (create Thought)
4. Search codebase for correct patterns
5. Self-critique the proposed fix
6. Generate improved code with context
7. Repeat until valid or max_thoughts reached

Example:
    config = AIConfig.load()
    agent = GeneratorAgent(config)
    
    code = await agent.generate(
        generator_type="page",
        name="products",
        answers={"purpose": "Product listing", "data": "Product cards"}
    )
"""

import asyncio
import json
import re
from typing import Any, Dict, List, Optional

from .config import AIConfig, ThoughtConfig, ThoughtDepth, ValidationLevel
from .thought import Thought, ThoughtThread, create_thought_from_ai_response
from .reasoning import (
    THOUGHT_PROMPT,
    SHALLOW_THOUGHT_PROMPT,
    MEDIUM_THOUGHT_PROMPT,
    SELF_CRITIQUE_PROMPT,
    GENERATION_WITH_CONTEXT_PROMPT,
    INITIAL_GENERATION_PROMPT,
    format_generation_prompt,
)
from .validator import CodeValidator, ValidationResult
from .search import CodebaseSearch


# ============================================
# Exceptions
# ============================================

class GenerationError(Exception):
    """
    Raised when code generation fails after all attempts.
    
    Attributes:
        message: Error message
        reasoning: Full reasoning chain from the thought thread
        last_code: The last generated code
        last_errors: Errors from the last validation
        thought_thread: The complete thought thread
    """
    
    def __init__(
        self,
        message: str,
        reasoning: str = "",
        last_code: str = "",
        last_errors: List[str] = None,
        thought_thread: Optional[ThoughtThread] = None,
    ):
        super().__init__(message)
        self.reasoning = reasoning
        self.last_code = last_code
        self.last_errors = last_errors or []
        self.thought_thread = thought_thread
    
    def __str__(self) -> str:
        parts = [super().__str__()]
        
        if self.last_errors:
            parts.append("\nLast errors:")
            for error in self.last_errors:
                parts.append(f"  - {error}")
        
        if self.reasoning:
            parts.append(f"\nReasoning:\n{self.reasoning}")
        
        return "\n".join(parts)


# ============================================
# Generator Agent
# ============================================

class GeneratorAgent:
    """
    AI-powered code generator with thought thread reasoning.
    
    The agent uses a chain-of-thought approach to:
    1. Generate code
    2. Validate it
    3. Think about errors (not just retry)
    4. Search for correct patterns
    5. Self-critique solutions
    6. Generate improved code
    
    Attributes:
        config: AIConfig with model and thought settings
        validator: CodeValidator for checking generated code
        searcher: CodebaseSearch for finding patterns
    
    Example:
        config = AIConfig(
            model="claude-sonnet-4-20250514",
            thought=ThoughtConfig(max_thoughts=5, thought_depth="deep")
        )
        
        agent = GeneratorAgent(config)
        code = await agent.generate("page", "products", {"purpose": "..."})
    """
    
    def __init__(self, config: AIConfig):
        """
        Initialize the agent.
        
        Args:
            config: AIConfig with settings
        """
        self.config = config
        self.validator = CodeValidator(
            level=ValidationLevel(config.validation_level)
            if isinstance(config.validation_level, str)
            else config.validation_level
        )
        self.searcher = CodebaseSearch()
        self._client = None
    
    def _get_client(self):
        """Get or create Anthropic client."""
        if self._client is None:
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "Install anthropic to use AI generation:\n"
                    "  pip install anthropic\n"
                    "Or add 'anthropic' to pynext.requirements.txt"
                )
            
            if not self.config.api_key:
                raise ValueError(
                    "Anthropic API key required.\n"
                    "Set ANTHROPIC_API_KEY environment variable or pass --api-key"
                )
            
            self._client = anthropic.Anthropic(api_key=self.config.api_key)
        
        return self._client
    
    async def generate(
        self,
        generator_type: str,
        name: str,
        answers: Dict[str, str],
        verbose: bool = False,
    ) -> str:
        """
        Generate code with thought thread reasoning.
        
        Args:
            generator_type: Type to generate (page, component, etc.)
            name: Component name
            answers: User requirements/answers
            verbose: Print progress
        
        Returns:
            Valid generated Python code
        
        Raises:
            GenerationError: If valid code cannot be generated
        """
        # Build requirements string
        requirements = self._format_requirements(answers)
        
        if verbose:
            print(f"\n🤖 Generating {generator_type}: {name}...")
        
        # Step 1: Initial generation
        code = await self._generate_initial(generator_type, name, requirements)
        
        # Step 2: Validate
        result = self.validator.validate(code, generator_type)
        
        if result.valid:
            if verbose:
                print("✅ Generated valid code on first try!")
            return code
        
        if verbose:
            print(f"⚠️  Initial code has errors. Starting thought thread...")
        
        # Step 3: Start thought thread
        thread = ThoughtThread(
            initial_error=result.format_for_ai(),
            generator_type=generator_type,
            component_name=name,
            original_code=code,
        )
        
        # Step 4: Think and improve
        for i in range(self.config.thought.max_thoughts):
            if verbose:
                print(f"\n💭 Thought {i + 1}/{self.config.thought.max_thoughts}...")
            
            # Think about the error
            thought = await self._think(
                code=code,
                errors=result.errors,
                thread=thread,
                thought_num=i + 1,
            )
            thread.add_thought(thought)
            
            if verbose:
                print(f"   Observation: {thought.observation[:100]}...")
                print(f"   Confidence: {thought.confidence:.0%}")
            
            # Search codebase if enabled
            if self.config.thought.enable_codebase_search and thought.search_queries:
                if verbose:
                    print(f"   🔍 Searching: {thought.search_queries}")
                
                for query in thought.search_queries[:2]:  # Limit searches
                    results = self.searcher.search(query)
                    if results:
                        thread.add_search_result(
                            query,
                            self.searcher.format_results(results)
                        )
            
            # Self-critique if deep mode and enabled
            if (self.config.thought.thought_depth == ThoughtDepth.DEEP and
                self.config.thought.enable_self_critique):
                
                critique = await self._self_critique(thread, thought.hypothesis)
                thread.add_critique(critique)
                
                if verbose:
                    if "PROCEED" in critique:
                        print("   ✓ Self-critique: Confident in fix")
                    else:
                        print(f"   Self-critique: {critique[:100]}...")
            
            # Check if confidence is high enough
            if thought.confidence >= self.config.thought.confidence_threshold:
                if verbose:
                    print(f"\n🔄 Generating improved code with context...")
                
                # Generate with accumulated context
                code = await self._generate_with_context(
                    generator_type=generator_type,
                    name=name,
                    requirements=requirements,
                    thread=thread,
                )
                
                # Validate again
                result = self.validator.validate(code, generator_type)
                
                if result.valid:
                    if verbose:
                        print(f"✅ Generated valid code after {i + 1} thoughts!")
                    return code
                
                if verbose:
                    print(f"⚠️  Still has errors: {result.errors[0][:50]}...")
            else:
                if verbose:
                    print(f"   Confidence too low ({thought.confidence:.0%}), thinking more...")
        
        # Failed after all thoughts
        raise GenerationError(
            f"Could not generate valid code after {thread.get_thought_count()} thoughts",
            reasoning=thread.get_reasoning_chain(),
            last_code=code,
            last_errors=result.errors,
            thought_thread=thread,
        )
    
    def _format_requirements(self, answers: Dict[str, str]) -> str:
        """Format user answers into requirements string."""
        return "\n".join(f"- {k}: {v}" for k, v in answers.items() if v)
    
    async def _generate_initial(
        self,
        generator_type: str,
        name: str,
        requirements: str,
    ) -> str:
        """Generate initial code without context."""
        prompt = INITIAL_GENERATION_PROMPT.format(
            generator_type=generator_type,
            name=name,
            requirements=requirements,
        )
        
        response = await self._call_ai(prompt)
        return self._extract_code(response)
    
    async def _generate_with_context(
        self,
        generator_type: str,
        name: str,
        requirements: str,
        thread: ThoughtThread,
    ) -> str:
        """Generate code with accumulated context from thinking."""
        prompt = format_generation_prompt(
            generator_type=generator_type,
            name=name,
            requirements=requirements,
            reasoning_chain=thread.get_reasoning_chain(),
            codebase_context=thread.context_accumulated,
        )
        
        response = await self._call_ai(prompt, max_tokens=4000)
        return self._extract_code(response)
    
    async def _think(
        self,
        code: str,
        errors: List[str],
        thread: ThoughtThread,
        thought_num: int,
    ) -> Thought:
        """Generate a thought about the errors."""
        # Choose prompt based on depth
        depth = self.config.thought.thought_depth
        if isinstance(depth, ThoughtDepth):
            depth = depth.value
        
        if depth == "shallow":
            prompt = SHALLOW_THOUGHT_PROMPT.format(
                error="\n".join(errors),
                code=code,
            )
        elif depth == "medium":
            prompt = MEDIUM_THOUGHT_PROMPT.format(
                previous_thoughts=thread.get_reasoning_chain(),
                error="\n".join(errors),
                code=code,
            )
        else:  # deep
            prompt = THOUGHT_PROMPT.format(
                previous_thoughts=thread.get_reasoning_chain(),
                error="\n".join(errors),
                code=code,
            )
        
        response = await self._call_ai(prompt, max_tokens=1500)
        
        # Parse JSON response
        thought_data = self._parse_thought_response(response)
        
        return create_thought_from_ai_response(thought_num, thought_data)
    
    async def _self_critique(
        self,
        thread: ThoughtThread,
        hypothesis: str,
    ) -> str:
        """Have the AI critique its own solution."""
        prompt = SELF_CRITIQUE_PROMPT.format(
            thoughts=thread.get_reasoning_chain(),
            hypothesis=hypothesis,
        )
        
        response = await self._call_ai(prompt, max_tokens=500)
        return response.strip()
    
    async def _call_ai(
        self,
        prompt: str,
        max_tokens: int = 2000,
        system: str = "",
    ) -> str:
        """Call the Anthropic API."""
        client = self._get_client()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        def make_call():
            return client.messages.create(
                model=self.config.model,
                max_tokens=max_tokens,
                system=system if system else "You are a PyNext expert.",
                messages=[{"role": "user", "content": prompt}],
            )
        
        message = await loop.run_in_executor(None, make_call)
        return message.content[0].text
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from AI response."""
        # Try to find python code block
        if "```python" in response:
            start = response.find("```python") + 9
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()
        
        # Try generic code block
        if "```" in response:
            start = response.find("```") + 3
            # Skip language identifier if present
            if response[start:start+20].strip().split()[0].isalpha():
                newline = response.find("\n", start)
                if newline > 0:
                    start = newline + 1
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()
        
        # Return as-is if no code block found
        return response.strip()
    
    def _parse_thought_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON thought response from AI.
        
        FUNDAMENTAL: Uses proper brace matching for nested JSON extraction.
        """
        response = response.strip()
        
        # Try to parse the whole response first (fastest path)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Find and extract JSON object with proper brace matching
        json_str = self._extract_json_object(response)
        if json_str:
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Fallback: extract key-value pairs manually
        result = {
            "observation": "Could not parse AI response",
            "reasoning": response[:500],
            "hypothesis": "Review and fix the error",
            "search_queries": [],
            "confidence": 0.3,
        }
        
        # Try to extract confidence using simple search
        confidence = self._extract_confidence(response)
        if confidence is not None:
            result["confidence"] = confidence
        
        return result
    
    def _extract_json_object(self, text: str) -> Optional[str]:
        """Extract a JSON object from text using proper brace matching.
        
        FUNDAMENTAL: Handles nested braces correctly, unlike regex [^{}]*.
        """
        # Find the first '{'
        start = text.find('{')
        if start == -1:
            return None
        
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        
        return None
    
    def _extract_confidence(self, text: str) -> Optional[float]:
        """Extract confidence value from text."""
        # Look for patterns like: confidence: 0.8, "confidence": 0.8
        text_lower = text.lower()
        idx = text_lower.find('confidence')
        if idx == -1:
            return None
        
        # Find the number after 'confidence'
        after = text[idx + 10:]  # len('confidence') = 10
        
        # Skip non-digit characters until we find a number
        num_start = -1
        for i, char in enumerate(after):
            if char.isdigit() or char == '.':
                num_start = i
                break
        
        if num_start == -1:
            return None
        
        # Extract the number
        num_end = num_start
        has_dot = False
        for i in range(num_start, len(after)):
            char = after[i]
            if char.isdigit():
                num_end = i + 1
            elif char == '.' and not has_dot:
                has_dot = True
                num_end = i + 1
            else:
                break
        
        try:
            return float(after[num_start:num_end])
        except ValueError:
            return None


# ============================================
# Synchronous Wrapper
# ============================================

def generate_with_agent(
    generator_type: str,
    name: str,
    answers: Dict[str, str],
    config: Optional[AIConfig] = None,
    verbose: bool = False,
) -> str:
    """
    Synchronous wrapper for GeneratorAgent.generate().
    
    Args:
        generator_type: Type to generate (page, component, etc.)
        name: Component name
        answers: User requirements/answers
        config: AIConfig (optional, loads from env if not provided)
        verbose: Print progress
    
    Returns:
        Valid generated Python code
    
    Example:
        code = generate_with_agent(
            "page",
            "products",
            {"purpose": "Product listing"},
            verbose=True
        )
    """
    if config is None:
        config = AIConfig.load()
    
    agent = GeneratorAgent(config)
    return asyncio.run(agent.generate(generator_type, name, answers, verbose))

