"""
Thought Thread System for AI Code Generation.

Implements a chain-of-thought reasoning system where each thought builds
on the previous, allowing the AI to deeply analyze mistakes rather than
blindly retrying.

Key concepts:
- Thought: A single reasoning step with observation, reasoning, hypothesis
- ThoughtThread: A chain of thoughts that accumulates context
- Progressive Understanding: Each thought adds to the knowledge base

Example:
    # Create a thought thread
    thread = ThoughtThread()
    
    # Add thoughts as the AI reasons
    thought = Thought(
        id=1,
        observation="SyntaxError: invalid syntax at line 5",
        reasoning="The div() function was called without parentheses...",
        hypothesis="Add parentheses around children elements",
        search_queries=["PyNext div syntax", "element children"],
        confidence=0.85
    )
    thread.add_thought(thought)
    
    # Get the full reasoning chain for context
    chain = thread.get_reasoning_chain()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================
# Thought Data Structure
# ============================================

@dataclass
class Thought:
    """
    A single step in the reasoning chain.
    
    Each thought represents one cycle of the AI's analysis:
    1. Observe the error/issue
    2. Reason about WHY it happened
    3. Form a hypothesis about the fix
    4. Identify what to search for confirmation
    5. Estimate confidence in the solution
    
    Attributes:
        id: Sequential thought number (1, 2, 3...)
        observation: What the AI observed (error message, pattern, etc.)
        reasoning: WHY this happened - the chain of thought
        hypothesis: What specific change will fix it
        search_queries: What to search in PyNext docs/code
        confidence: 0.0-1.0, how confident in the fix
        timestamp: When this thought was created
        search_results: Results from codebase search (if performed)
        critique: Self-critique of this thought (if performed)
    
    Example:
        thought = Thought(
            id=1,
            observation="NameError: name 'Signal' is not defined",
            reasoning=(
                "The code uses Signal() but doesn't import it. "
                "In PyNext, Signal must be imported from pynext.core. "
                "This is a common mistake when writing reactive components."
            ),
            hypothesis="Add 'from pynext import Signal' at the top of the file",
            search_queries=["PyNext Signal import", "reactive state"],
            confidence=0.95
        )
    """
    id: int
    observation: str
    reasoning: str
    hypothesis: str
    search_queries: List[str] = field(default_factory=list)
    confidence: float = 0.5
    timestamp: datetime = field(default_factory=datetime.utcnow)
    search_results: Optional[str] = None
    critique: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate thought data."""
        if not 0.0 <= self.confidence <= 1.0:
            self.confidence = max(0.0, min(1.0, self.confidence))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "observation": self.observation,
            "reasoning": self.reasoning,
            "hypothesis": self.hypothesis,
            "search_queries": self.search_queries,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "search_results": self.search_results,
            "critique": self.critique,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Thought":
        """Create Thought from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.utcnow()
        
        return cls(
            id=data["id"],
            observation=data["observation"],
            reasoning=data["reasoning"],
            hypothesis=data["hypothesis"],
            search_queries=data.get("search_queries", []),
            confidence=data.get("confidence", 0.5),
            timestamp=timestamp,
            search_results=data.get("search_results"),
            critique=data.get("critique"),
        )
    
    def format_short(self) -> str:
        """Format thought as a short summary."""
        return f"Thought {self.id} ({self.confidence:.0%}): {self.hypothesis[:100]}..."
    
    def format_full(self) -> str:
        """Format thought with full details."""
        lines = [
            f"## Thought {self.id} (Confidence: {self.confidence:.0%})",
            "",
            f"**Observation:** {self.observation}",
            "",
            f"**Reasoning:** {self.reasoning}",
            "",
            f"**Hypothesis:** {self.hypothesis}",
        ]
        
        if self.search_queries:
            lines.extend([
                "",
                f"**Search Queries:** {', '.join(self.search_queries)}",
            ])
        
        if self.search_results:
            lines.extend([
                "",
                f"**Search Results:**",
                self.search_results,
            ])
        
        if self.critique:
            lines.extend([
                "",
                f"**Self-Critique:** {self.critique}",
            ])
        
        return "\n".join(lines)


# ============================================
# Thought Thread
# ============================================

@dataclass
class ThoughtThread:
    """
    A chain of reasoning about code generation.
    
    The thought thread maintains the full history of the AI's reasoning
    process, accumulating context from searches and building understanding
    over multiple thought cycles.
    
    Attributes:
        thoughts: List of Thought objects in order
        context_accumulated: Growing context from codebase searches
        initial_error: The original error that started the thread
        generator_type: Type being generated (page, component, etc.)
        component_name: Name of the component being generated
        original_code: The first generated code that had errors
    
    Example:
        thread = ThoughtThread(
            initial_error="SyntaxError at line 5",
            generator_type="page",
            component_name="products"
        )
        
        # Add thoughts as AI reasons
        thread.add_thought(thought1)
        thread.add_thought(thought2)
        
        # Get full reasoning chain for AI context
        chain = thread.get_reasoning_chain()
        
        # Check if we should try generating
        if thread.should_attempt_generation():
            # AI is confident enough
            pass
    """
    thoughts: List[Thought] = field(default_factory=list)
    context_accumulated: str = ""
    initial_error: str = ""
    generator_type: str = ""
    component_name: str = ""
    original_code: str = ""
    started_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_thought(self, thought: Thought) -> None:
        """
        Add a thought to the chain.
        
        Args:
            thought: The Thought to add
        """
        self.thoughts.append(thought)
    
    def get_latest_thought(self) -> Optional[Thought]:
        """Get the most recent thought."""
        return self.thoughts[-1] if self.thoughts else None
    
    def get_highest_confidence_thought(self) -> Optional[Thought]:
        """Get the thought with highest confidence."""
        if not self.thoughts:
            return None
        return max(self.thoughts, key=lambda t: t.confidence)
    
    def get_reasoning_chain(self) -> str:
        """
        Format the full chain of thought for AI context.
        
        This is passed to the AI so it can see its previous reasoning
        and build on it rather than starting fresh.
        
        Returns:
            Formatted string with all thoughts
        """
        if not self.thoughts:
            return "No previous thoughts."
        
        parts = []
        for thought in self.thoughts:
            parts.append(
                f"### Thought {thought.id}\n"
                f"**Observed:** {thought.observation}\n"
                f"**Reasoning:** {thought.reasoning}\n"
                f"**Hypothesis:** {thought.hypothesis}\n"
                f"**Confidence:** {thought.confidence:.0%}"
            )
        
        return "\n\n".join(parts)
    
    def get_context_for_generation(self) -> str:
        """
        Get accumulated context for the next generation attempt.
        
        Combines:
        - All previous reasoning
        - Search results
        - Self-critiques
        
        Returns:
            Formatted context string
        """
        parts = [
            "## Previous Reasoning",
            self.get_reasoning_chain(),
        ]
        
        if self.context_accumulated:
            parts.extend([
                "",
                "## Information from PyNext Codebase",
                self.context_accumulated,
            ])
        
        # Add any critiques
        critiques = [t.critique for t in self.thoughts if t.critique]
        if critiques:
            parts.extend([
                "",
                "## Self-Critiques",
                "\n".join(f"- {c}" for c in critiques),
            ])
        
        return "\n\n".join(parts)
    
    def should_attempt_generation(self, threshold: float = 0.8) -> bool:
        """
        Check if we should attempt code generation.
        
        Args:
            threshold: Minimum confidence required (default: 0.8)
        
        Returns:
            True if latest thought has sufficient confidence
        """
        latest = self.get_latest_thought()
        return latest is not None and latest.confidence >= threshold
    
    def add_search_result(self, query: str, result: str) -> None:
        """
        Add search result to accumulated context.
        
        Args:
            query: The search query
            result: The search results
        """
        self.context_accumulated += f"\n\n### Search: {query}\n{result}"
        
        # Also attach to the latest thought
        if self.thoughts:
            latest = self.thoughts[-1]
            if latest.search_results:
                latest.search_results += f"\n\n{query}: {result}"
            else:
                latest.search_results = f"{query}: {result}"
    
    def add_critique(self, critique: str) -> None:
        """
        Add self-critique to the latest thought.
        
        Args:
            critique: The self-critique text
        """
        if self.thoughts:
            self.thoughts[-1].critique = critique
    
    def get_thought_count(self) -> int:
        """Get number of thoughts in the thread."""
        return len(self.thoughts)
    
    def get_total_duration(self) -> float:
        """Get total time spent thinking in seconds."""
        if not self.thoughts:
            return 0.0
        return (datetime.utcnow() - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "thoughts": [t.to_dict() for t in self.thoughts],
            "context_accumulated": self.context_accumulated,
            "initial_error": self.initial_error,
            "generator_type": self.generator_type,
            "component_name": self.component_name,
            "original_code": self.original_code,
            "started_at": self.started_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThoughtThread":
        """Create ThoughtThread from dictionary."""
        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        elif started_at is None:
            started_at = datetime.utcnow()
        
        return cls(
            thoughts=[Thought.from_dict(t) for t in data.get("thoughts", [])],
            context_accumulated=data.get("context_accumulated", ""),
            initial_error=data.get("initial_error", ""),
            generator_type=data.get("generator_type", ""),
            component_name=data.get("component_name", ""),
            original_code=data.get("original_code", ""),
            started_at=started_at,
        )
    
    def format_summary(self) -> str:
        """Format a summary of the thought thread."""
        lines = [
            f"Thought Thread: {self.component_name} ({self.generator_type})",
            f"Thoughts: {len(self.thoughts)}",
            f"Duration: {self.get_total_duration():.1f}s",
        ]
        
        if self.thoughts:
            best = self.get_highest_confidence_thought()
            if best:
                lines.append(f"Best confidence: {best.confidence:.0%}")
        
        return "\n".join(lines)
    
    def format_full_report(self) -> str:
        """Format a full report of the reasoning process."""
        lines = [
            "# Thought Thread Report",
            "",
            f"**Component:** {self.component_name}",
            f"**Type:** {self.generator_type}",
            f"**Total Thoughts:** {len(self.thoughts)}",
            f"**Duration:** {self.get_total_duration():.1f}s",
            "",
            "## Initial Error",
            self.initial_error or "None",
            "",
            "## Reasoning Process",
        ]
        
        for thought in self.thoughts:
            lines.append("")
            lines.append(thought.format_full())
        
        if self.context_accumulated:
            lines.extend([
                "",
                "## Accumulated Context",
                self.context_accumulated,
            ])
        
        return "\n".join(lines)


# ============================================
# Helper Functions
# ============================================

def create_thought_from_ai_response(
    thought_id: int,
    response: Dict[str, Any]
) -> Thought:
    """
    Create a Thought from AI JSON response.
    
    Expected response format:
    {
        "observation": "...",
        "reasoning": "...",
        "hypothesis": "...",
        "search_queries": ["..."],
        "confidence": 0.X
    }
    
    Args:
        thought_id: Sequential thought number
        response: Parsed JSON from AI
    
    Returns:
        Thought object
    """
    return Thought(
        id=thought_id,
        observation=response.get("observation", "No observation provided"),
        reasoning=response.get("reasoning", "No reasoning provided"),
        hypothesis=response.get("hypothesis", "No hypothesis provided"),
        search_queries=response.get("search_queries", []),
        confidence=float(response.get("confidence", 0.5)),
    )

