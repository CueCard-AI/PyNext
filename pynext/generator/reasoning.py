"""
Reasoning Prompts for AI Code Generation.

Contains the prompts used by the AI to:
1. Think deeply about errors (THOUGHT_PROMPT)
2. Self-critique solutions (SELF_CRITIQUE_PROMPT)
3. Generate improved code (GENERATION_WITH_CONTEXT_PROMPT)

These prompts guide the AI through a structured chain-of-thought
reasoning process rather than just retrying blindly.

The prompts are designed to be:
- Clear and specific about what's expected
- Structured to produce parseable JSON responses
- Encouraging of deep analysis rather than surface fixes
"""

# ============================================
# Thought Prompt - Analyze Errors
# ============================================

THOUGHT_PROMPT = """You are debugging PyNext code. Think step by step.

## Previous Thoughts
{previous_thoughts}

## Current Error
{error}

## Generated Code
```python
{code}
```

## PyNext Framework Context
PyNext is a Python web framework with:
- Fine-grained reactivity (SolidJS principles)
- Python syntax for HTML: div(), h1(), button(), span()
- Signals for state: Signal(0), count.set(), count()
- Tailwind CSS via class_ parameter
- Decorators: @island, @action, @api

## Instructions
Think deeply about this error. Don't just identify it - understand WHY it happened.

Respond with your thought process:

1. **Observation**: What exactly went wrong? Quote the specific problematic code.

2. **Reasoning**: WHY did this happen? Consider:
   - Did I misunderstand a PyNext concept?
   - Did I use wrong syntax/API?
   - Did I make an assumption that was incorrect?
   - What PyNext pattern should I have used instead?

3. **Hypothesis**: Based on my reasoning, what specific change will fix this?
   Be precise - don't just say "fix the error", explain the exact fix.

4. **Search Query**: What should I search for in PyNext docs to confirm my hypothesis?

5. **Confidence**: 0-100%, how confident am I this will work?

Respond in JSON format ONLY:
{{"observation": "...", "reasoning": "...", "hypothesis": "...", "search_queries": ["query1", "query2"], "confidence": 0.X}}
"""


# ============================================
# Self-Critique Prompt
# ============================================

SELF_CRITIQUE_PROMPT = """Review your previous thoughts and proposed fix.

## Your Reasoning Chain
{thoughts}

## Proposed Fix
{hypothesis}

## PyNext Best Practices
- Always import from pynext: Signal, Computed, Effect, div, button, etc.
- Use class_ not class for CSS classes
- Signals are called like functions: count() not count
- Signal.set() to update: count.set(count() + 1)
- @island decorator for client-side interactivity
- @action for server mutations
- @api for API routes

Now critique yourself honestly:

1. **Potential Issues**: What could be wrong with this fix?
2. **Edge Cases**: Are there edge cases I'm not considering?
3. **Simpler Solution**: Is there a simpler/more PyNext-idiomatic solution?
4. **Missing Pieces**: Am I missing any imports, decorators, or boilerplate?

If you find significant issues, explain them in detail.
If you're confident the fix is correct, respond with exactly: PROCEED

Response:"""


# ============================================
# Generation with Context Prompt
# ============================================

GENERATION_WITH_CONTEXT_PROMPT = """You are generating PyNext code with the benefit of previous analysis.

## Component Details
- Type: {generator_type}
- Name: {name}

## User Requirements
{requirements}

## Previous Reasoning (IMPORTANT - Learn from this!)
{reasoning_chain}

## Information from PyNext Codebase
{codebase_context}

## PyNext Framework Reference

### Imports
```python
from pynext import div, h1, p, button, span, input_, form, a, img, ul, li
from pynext import Signal, Computed, Effect
from pynext.islands import island
from pynext.actions import action, ActionError
from pynext.api import api, Request, Response
```

### Signals (State)
```python
count = Signal(0)           # Create
current = count()           # Read (call like function)
count.set(count() + 1)      # Write
doubled = Computed(lambda: count() * 2)  # Derived
```

### Elements
```python
div(class_="container")(    # Note: class_ not class
    h1("Title"),
    p("Paragraph"),
)
button(on_click=handler)("Click me")
input_(type_="text", name="email")  # Note: input_ not input
```

### Islands (Client Interactivity)
```python
@island
def Counter():
    count = Signal(0)
    return button(on_click=lambda: count.set(count() + 1))(
        f"Count: {{count()}}"
    )
```

### Server Actions
```python
@action
async def create_user(form_data: dict):
    if not form_data.get("email"):
        raise ActionError("Email required", field="email")
    return {{"success": True}}
```

## Instructions
Generate the {generator_type} incorporating what you learned from the reasoning chain.
Pay special attention to the errors identified and the fixes proposed.

Return ONLY valid Python code inside a ```python code block.
No explanations before or after the code block.

The code must:
1. Be syntactically correct Python
2. Use correct PyNext imports
3. Follow PyNext patterns exactly
4. Address all issues from the reasoning chain
"""


# ============================================
# Initial Generation Prompt (No Context)
# ============================================

INITIAL_GENERATION_PROMPT = """You are a PyNext expert generating a {generator_type}.

## PyNext Framework Overview

PyNext is a Python web framework similar to Next.js but with:
- Fine-grained reactivity (SolidJS principles - no virtual DOM, only affected DOM updates)
- Python syntax for HTML: div(), h1(), button(), span(), etc.
- Tailwind CSS for styling via class_ parameter
- File-based routing like Next.js

## Core Patterns

### HTML Elements
```python
from pynext import div, h1, p, button, span, input_, form, a, img, ul, li

# Basic usage - children go in second call
div(class_="container")(
    h1("Title"),
    p("Paragraph"),
)

# Attributes
button(class_="btn", type_="submit", on_click=handler)("Click")
input_(type_="text", name="email", placeholder="Email")
a(href="/about")("About")
```

### Signals (Fine-grained State)
```python
from pynext import Signal, Computed, Effect

# State that tracks dependencies
count = Signal(0)

# Read: call like a function
current = count()

# Write: use .set()
count.set(count() + 1)

# Derived values (auto-update)
doubled = Computed(lambda: count() * 2)

# Side effects
Effect(lambda: print(f"Count: {{count()}}"))
```

### Islands (Client Interactivity)
```python
from pynext.islands import island

@island  # Makes this component hydrate on client
def Counter():
    count = Signal(0)
    return button(on_click=lambda: count.set(count() + 1))(
        f"Count: {{count()}}"
    )
```

### Server Actions
```python
from pynext.actions import action, ActionError

@action
async def create_user(form_data: dict):
    if not form_data.get("email"):
        raise ActionError("Email required", field="email")
    # Create user...
    return {{"success": True}}
```

### API Routes
```python
from pynext.api import api, Request, Response

@api
async def GET(request: Request):
    return Response.json({{"items": []}})

@api
async def POST(request: Request):
    data = await request.json()
    return Response.json({{"created": data}}, status=201)
```

### Layouts & Pages
```python
# pages/layout.py - wraps all pages in this directory
def layout(children):
    return div(class_="min-h-screen")(
        nav(...),
        main(children),
        footer(...),
    )

# pages/index.py - the page content
def page():
    return div(
        h1("Welcome"),
        p("This is my page"),
    )
```

## User Requirements
{requirements}

## Instructions
Generate a complete, working, production-ready {generator_type} named '{name}'.

Requirements:
1. Use proper PyNext imports
2. Use class_ for CSS classes (not class)
3. Use input_ for input elements (not input)
4. Signals are called like functions: count() to read, count.set() to write
5. Use Tailwind CSS classes for styling
6. Include helpful docstrings

Return ONLY valid Python code inside a ```python code block.
No explanations before or after the code block.
"""


# ============================================
# Error Analysis Prompt (Shallow Mode)
# ============================================

SHALLOW_THOUGHT_PROMPT = """Quickly analyze this PyNext code error.

## Error
{error}

## Code
```python
{code}
```

Identify:
1. What's wrong (be specific)
2. How to fix it (be precise)

Respond in JSON:
{{"observation": "...", "hypothesis": "...", "confidence": 0.X}}
"""


# ============================================
# Medium Depth Prompt
# ============================================

MEDIUM_THOUGHT_PROMPT = """Analyze this PyNext code error.

## Previous Analysis
{previous_thoughts}

## Error
{error}

## Code
```python
{code}
```

Think about:
1. What exactly went wrong?
2. Why did this happen?
3. What's the fix?

Respond in JSON:
{{"observation": "...", "reasoning": "...", "hypothesis": "...", "search_queries": ["..."], "confidence": 0.X}}
"""


# ============================================
# Helper: Get Prompt by Depth
# ============================================

def get_thought_prompt(depth: str) -> str:
    """
    Get the appropriate thought prompt for the given depth.
    
    Args:
        depth: "shallow", "medium", or "deep"
    
    Returns:
        The prompt template string
    """
    prompts = {
        "shallow": SHALLOW_THOUGHT_PROMPT,
        "medium": MEDIUM_THOUGHT_PROMPT,
        "deep": THOUGHT_PROMPT,
    }
    return prompts.get(depth, THOUGHT_PROMPT)


def format_thought_prompt(
    depth: str,
    error: str,
    code: str,
    previous_thoughts: str = "No previous thoughts."
) -> str:
    """
    Format a thought prompt with the given parameters.
    
    Args:
        depth: "shallow", "medium", or "deep"
        error: The error message
        code: The generated code
        previous_thoughts: Previous reasoning (for medium/deep)
    
    Returns:
        Formatted prompt string
    """
    prompt = get_thought_prompt(depth)
    return prompt.format(
        error=error,
        code=code,
        previous_thoughts=previous_thoughts,
    )


def format_generation_prompt(
    generator_type: str,
    name: str,
    requirements: str,
    reasoning_chain: str = "",
    codebase_context: str = ""
) -> str:
    """
    Format a generation prompt.
    
    If reasoning_chain is provided, uses the context-aware prompt.
    Otherwise uses the initial generation prompt.
    
    Args:
        generator_type: Type (page, component, etc.)
        name: Component name
        requirements: User requirements
        reasoning_chain: Previous reasoning (optional)
        codebase_context: Context from codebase search (optional)
    
    Returns:
        Formatted prompt string
    """
    if reasoning_chain:
        return GENERATION_WITH_CONTEXT_PROMPT.format(
            generator_type=generator_type,
            name=name,
            requirements=requirements,
            reasoning_chain=reasoning_chain,
            codebase_context=codebase_context or "No additional context.",
        )
    else:
        return INITIAL_GENERATION_PROMPT.format(
            generator_type=generator_type,
            name=name,
            requirements=requirements,
        )

