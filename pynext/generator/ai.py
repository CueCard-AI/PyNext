"""
AI-assisted component generation.

Uses Anthropic Claude with leading questions to understand
exactly what the user wants before generating.

Features:
- Leading questions by generator type
- AI evaluates if enough info was gathered
- Follow-up questions for missing details
- High-quality code generation

Example:
    pynext g page products --ai
    
    🤖 AI Assistant: Let me ask a few questions...
    
    What is this page for?
    → E-commerce product listing
    
    What data will it display?
    → Product cards with image, title, price
    
    🤖 I have a few more questions...
    → Should products be filterable?
    → How many products per page?
    
    🤖 Generating your component...
    
    ✅ Created: pages/products.py
"""

import os
import re
from typing import Dict, List, Optional


# ============================================
# Leading Questions by Type
# ============================================

AI_QUESTIONS: Dict[str, List[tuple]] = {
    "page": [
        ("purpose", "What is this page for? (e.g., blog listing, user profile, dashboard)"),
        ("data", "What data will this page display? (e.g., list of posts, user info)"),
        ("actions", "What can users do on this page? (e.g., click items, filter, search)"),
        ("style", "Any specific design style? (e.g., minimal, card-based, table)"),
    ],
    "component": [
        ("purpose", "What does this component do? (e.g., display a card, form input)"),
        ("props", "What props should it accept? (e.g., title, onClick, items)"),
        ("interactive", "Does it need client-side interactivity? [y/N]"),
        ("variants", "Any variants needed? (e.g., sizes, colors, states)"),
    ],
    "island": [
        ("purpose", "What interactive feature does this island provide?"),
        ("state", "What state does it manage? (e.g., count, form data, toggle)"),
        ("events", "What user interactions? (e.g., click, input, drag)"),
        ("effects", "Any side effects? (e.g., API calls, localStorage, animations)"),
    ],
    "api": [
        ("method", "HTTP methods? [GET/POST/PUT/DELETE]"),
        ("purpose", "What does this endpoint do? (e.g., fetch users, create post)"),
        ("params", "What parameters/body does it accept?"),
        ("response", "What does it return? (e.g., JSON list, single object)"),
    ],
    "action": [
        ("purpose", "What mutation does this action perform?"),
        ("input", "What data does it receive from the form?"),
        ("validation", "Any validation rules? (e.g., required fields, email format)"),
        ("result", "What happens after success? (e.g., redirect, show message)"),
    ],
    "layout": [
        ("sections", "What sections should the layout have? (e.g., nav, sidebar, footer)"),
        ("navigation", "What navigation links are needed?"),
        ("responsive", "Any special mobile layout considerations?"),
    ],
    "template": [
        ("animation", "What animation on page enter? (e.g., fade, slide, none)"),
        ("purpose", "Why use template instead of layout? (e.g., reset state, animations)"),
    ],
    "loading": [
        ("content_type", "What content is being loaded? (e.g., cards, table, text)"),
        ("skeleton_style", "Skeleton style preference? (e.g., shimmer, pulse, static)"),
    ],
    "error": [
        ("error_types", "What errors might occur? (e.g., network, auth, not found)"),
        ("recovery", "How can users recover? (e.g., retry, go back, login)"),
    ],
    "middleware": [
        ("purpose", "What does this middleware do? (e.g., auth check, logging)"),
        ("routes", "Which routes should it apply to? (e.g., /dashboard/*, /api/*)"),
        ("conditions", "What conditions trigger redirects/blocks?"),
    ],
    "hook": [
        ("purpose", "What logic does this hook encapsulate?"),
        ("inputs", "What parameters does it accept?"),
        ("outputs", "What does it return? (e.g., state, functions, computed values)"),
    ],
}


# ============================================
# AI Interview
# ============================================

def ai_interview(
    generator_type: str,
    name: str,
    api_key: Optional[str] = None,
) -> Dict[str, str]:
    """
    Conduct an AI-guided interview to understand requirements.
    
    Uses AI to evaluate if enough info was gathered and asks follow-ups.
    
    Args:
        generator_type: Type of component
        name: Component name
        api_key: Anthropic API key for follow-up evaluation
    
    Returns:
        Dict of answers keyed by question id
    
    Example:
        answers = ai_interview("page", "products")
        # User is asked questions interactively
        # Returns {"purpose": "...", "data": "...", ...}
    """
    questions = AI_QUESTIONS.get(generator_type, [])
    answers = {}
    
    print(f"\n🤖 AI Assistant: Let me ask a few questions about your {generator_type}...\n")
    
    # Phase 1: Ask standard questions
    for q_id, question in questions:
        answer = input(f"  {question}\n  → ").strip()
        if answer:
            answers[q_id] = answer
    
    # Phase 2: AI evaluates if we have enough info
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if key and answers:
        follow_ups = evaluate_completeness(generator_type, name, answers, key)
        
        # Phase 3: Ask AI-generated follow-up questions
        if follow_ups:
            print("\n🤖 I have a few more questions to make sure I understand...\n")
            for i, follow_up in enumerate(follow_ups, 1):
                answer = input(f"  {follow_up}\n  → ").strip()
                if answer:
                    answers[f"followup_{i}"] = answer
    
    # Phase 4: Optional free-form
    extra = input("\n  Anything else I should know? (press Enter to skip)\n  → ").strip()
    if extra:
        answers["extra"] = extra
    
    return answers


def evaluate_completeness(
    generator_type: str,
    name: str,
    answers: Dict[str, str],
    api_key: str,
) -> List[str]:
    """
    Use AI to evaluate if we have enough information.
    
    Returns a list of follow-up questions if more info is needed.
    Returns empty list if we have enough.
    
    Args:
        generator_type: Type of component
        name: Component name
        answers: Current answers from user
        api_key: Anthropic API key
    
    Returns:
        List of follow-up questions (empty if sufficient)
    """
    try:
        import anthropic
    except ImportError:
        return []  # Can't evaluate without anthropic
    
    client = anthropic.Anthropic(api_key=api_key)
    
    context = "\n".join(f"- {k}: {v}" for k, v in answers.items())
    
    eval_prompt = f"""You are helping generate a PyNext {generator_type} named '{name}'.

The user provided these requirements:
{context}

Evaluate if this is enough information to generate a high-quality, production-ready {generator_type}.

Consider:
1. Is the purpose clear enough to implement correctly?
2. Are there ambiguities that could lead to wrong assumptions?
3. Are critical details missing? (data structure, user interactions, edge cases, error handling)
4. Would a developer need to guess at important decisions?

If MORE information is needed, respond with 1-3 SHORT, SPECIFIC follow-up questions (one per line).
Each question should be something that would significantly improve the generated code.

If you have ENOUGH information to generate good code, respond with exactly: SUFFICIENT

Examples of good follow-up questions:
- "Should the search filter results in real-time as the user types, or on button click?"
- "What fields should each product card display? (image, title, price, description, rating?)"
- "Should unauthenticated users be redirected to login or see a limited view?"
- "What happens when the list is empty - show a message or hide the section?"

Examples of BAD questions (too vague, already covered, or unnecessary):
- "Can you tell me more?" (too vague)
- "What does it do?" (already asked)
- "What color should buttons be?" (too detailed for scaffolding)

Respond with ONLY the questions (one per line) or SUFFICIENT. No other text."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": eval_prompt}],
        )
        
        response = message.content[0].text.strip()
        
        if "SUFFICIENT" in response.upper():
            return []
        
        # Parse questions (one per line)
        questions = []
        for line in response.split("\n"):
            line = line.strip()
            # Remove common prefixes
            line = re.sub(r'^[\d\.\-\*•]+\s*', '', line)
            line = line.strip()
            
            if line and "?" in line and len(line) > 10:
                questions.append(line)
        
        return questions[:3]  # Max 3 follow-ups
        
    except Exception as e:
        print(f"  (Could not evaluate completeness: {e})")
        return []


# ============================================
# AI Code Generation
# ============================================

def generate_with_ai(
    generator_type: str,
    name: str,
    answers: Dict[str, str],
    api_key: Optional[str] = None,
) -> str:
    """
    Generate component using AI with gathered context.
    
    Args:
        generator_type: Type (page, component, etc.)
        name: Component name
        answers: Dict from ai_interview()
        api_key: Anthropic API key
    
    Returns:
        Generated Python code
    
    Raises:
        ValueError: If API key is missing
        ImportError: If anthropic is not installed
    
    Example:
        answers = ai_interview("page", "products")
        code = generate_with_ai("page", "products", answers)
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "Anthropic API key required.\n"
            "Set ANTHROPIC_API_KEY environment variable or pass --api-key"
        )
    
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "Install anthropic to use AI generation:\n"
            "  pip install anthropic\n"
            "Or add 'anthropic' to pynext.requirements.txt"
        )
    
    client = anthropic.Anthropic(api_key=key)
    
    # Build context from answers
    context = "\n".join(f"- {k}: {v}" for k, v in answers.items())
    
    # System prompt with comprehensive PyNext context
    system = f"""You are a PyNext expert generating a {generator_type}.

## PyNext Framework Overview

PyNext is a Python web framework similar to Next.js but with:
- Fine-grained reactivity (SolidJS principles - no virtual DOM, only affected DOM updates)
- Python syntax for HTML: div(), h1(), button(), span(), etc.
- Tailwind CSS for styling via class_ parameter
- File-based routing like Next.js

## Core Concepts

### HTML Elements
```python
from pynext import div, h1, p, button, span, input_, form, a, img, ul, li

# Basic usage
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

# pages/blog.py - page component
metadata = Metadata(title="Blog", description="...")

async def get_data():
    return {{"posts": await fetch_posts()}}

def blog(data):
    return div(
        For(data["posts"], lambda post: PostCard(post))
    )
```

## Generation Rules

1. **Imports**: Only import what you use from pynext
2. **Styling**: Use Tailwind classes, no inline styles
3. **Type hints**: Include type hints for all function parameters
4. **Docstrings**: Add docstrings explaining what the component does
5. **Clean code**: Production-ready, no TODOs or placeholders
6. **Error handling**: Handle edge cases (empty lists, missing data)
7. **Accessibility**: Include aria labels, semantic HTML where appropriate

## Output Format

Return ONLY valid Python code inside a ```python code block.
No explanations before or after the code block."""

    user_prompt = f"""Create a {generator_type} named '{name}'.

Requirements from user:
{context}

Generate a complete, working, production-ready {generator_type} that fully implements these requirements.
Use best practices and make it look professional."""

    print("\n🤖 Generating your component...\n")
    
    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        
        return extract_code(message.content[0].text)
        
    except Exception as e:
        raise RuntimeError(f"AI generation failed: {e}")


def extract_code(response: str) -> str:
    """
    Extract Python code from AI response.
    
    Args:
        response: Full AI response text
    
    Returns:
        Extracted Python code
    """
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


# ============================================
# Quick Generation (Single Prompt)
# ============================================

def generate_quick(
    generator_type: str,
    name: str,
    description: str,
    api_key: Optional[str] = None,
) -> str:
    """
    Quick generation with a single description.
    
    For users who know exactly what they want.
    Skips the interview process.
    
    Args:
        generator_type: Type of component
        name: Component name
        description: Free-form description
        api_key: Anthropic API key
    
    Returns:
        Generated Python code
    
    Example:
        code = generate_quick(
            "page",
            "products",
            "E-commerce product grid with filtering and search"
        )
    """
    answers = {"description": description}
    return generate_with_ai(generator_type, name, answers, api_key)

