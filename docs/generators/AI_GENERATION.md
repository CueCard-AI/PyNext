# AI-Assisted Code Generation

PyNext includes an intelligent AI code generation system powered by Anthropic Claude. Unlike simple AI code generators that just output text, PyNext's generator uses **thought threads** - a chain-of-thought reasoning system that deeply analyzes errors and iteratively improves code until it's valid.

## Table of Contents

1. [Quick Start](#quick-start)
2. [How It Works](#how-it-works)
3. [Configuration](#configuration)
4. [Thought Threads](#thought-threads)
5. [Validation Levels](#validation-levels)
6. [CLI Reference](#cli-reference)
7. [Python API](#python-api)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Basic Usage

```bash
# Interactive AI generation with questions
pynext g page products --ai

# Quick generation with a prompt
pynext g page products --ai -p "E-commerce product grid with filtering"

# Verbose mode to see the reasoning process
pynext g page products --ai -p "Product grid" --verbose
```

### Environment Setup

```bash
# Required: Set your Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional: Set default model
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"

# Optional: Set default max thoughts
export PYNEXT_AI_MAX_THOUGHTS=5
```

---

## How It Works

PyNext's AI generation follows a unique **agentic loop** with chain-of-thought reasoning:

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Generation Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Generate Initial Code                                    │
│         ↓                                                    │
│  2. Validate (syntax, imports, patterns)                     │
│         ↓                                                    │
│     ┌───────┐                                                │
│     │ Valid │ ──────→ Return Code ✅                         │
│     └───────┘                                                │
│         │                                                    │
│         ↓ (if errors)                                        │
│                                                              │
│  3. Think About Error (create Thought)                       │
│     • What went wrong? (observation)                         │
│     • Why did it happen? (reasoning)                         │
│     • What will fix it? (hypothesis)                         │
│     • Confidence level (0-100%)                              │
│         ↓                                                    │
│  4. Search PyNext Codebase (if enabled)                      │
│     • Find correct patterns                                  │
│     • Get documentation examples                             │
│         ↓                                                    │
│  5. Self-Critique (if deep mode)                            │
│     • What could be wrong with this fix?                     │
│     • Are there edge cases?                                  │
│         ↓                                                    │
│  6. Generate Improved Code with Context                      │
│         ↓                                                    │
│  7. Repeat from step 2 until valid or max_thoughts reached   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why Thought Threads?

Traditional AI code generation just outputs code and hopes it works. If it doesn't, you have to manually debug and re-prompt. PyNext's approach is different:

1. **Deep Analysis**: Instead of blindly retrying, the AI thinks about *why* the error occurred
2. **Progressive Learning**: Each thought builds on previous reasoning
3. **Codebase Search**: The AI can search PyNext docs for correct patterns
4. **Self-Critique**: In deep mode, the AI reviews its own solutions before generating
5. **Confidence Tracking**: Only generates new code when confident in the fix

---

## Configuration

### Configuration Priority

Settings are loaded in this order (higher overrides lower):

| Priority | Source | Example |
|----------|--------|---------|
| 1 (highest) | CLI flags | `--model claude-opus-4-20250514` |
| 2 | Environment variables | `ANTHROPIC_MODEL=claude-opus-4` |
| 3 | Config file | `pynext.ai.toml` |
| 4 (lowest) | Default values | `claude-sonnet-4-20250514` |

### Environment Variables

```bash
# API Key (required)
ANTHROPIC_API_KEY=sk-ant-...

# Model selection
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Thought thread settings
PYNEXT_AI_MAX_THOUGHTS=5
PYNEXT_AI_THOUGHT_DEPTH=deep        # shallow, medium, deep
PYNEXT_AI_VALIDATION=full           # syntax, imports, full

# Feature toggles
PYNEXT_AI_CODEBASE_SEARCH=true
PYNEXT_AI_SELF_CRITIQUE=true
PYNEXT_AI_CONFIDENCE_THRESHOLD=0.8
```

### Config File (pynext.ai.toml)

```toml
[ai]
model = "claude-sonnet-4-20250514"
validation_level = "full"

[ai.thought]
max_thoughts = 5
thought_depth = "deep"
enable_codebase_search = true
enable_self_critique = true
confidence_threshold = 0.8
```

---

## Thought Threads

### Thought Depth Levels

| Level | Thoughts | Speed | Use Case |
|-------|----------|-------|----------|
| `shallow` | 1-2 | Fast | Simple fixes, quick prototyping |
| `medium` | 2-3 | Balanced | Standard generation |
| `deep` | 3-5 | Thorough | Complex components, production code |

### Shallow Mode

Fast generation with minimal analysis. Good for simple components.

```bash
pynext g component Button --ai --thought-depth shallow
```

What happens:
1. Generate code
2. If error: Identify error → Suggest fix → Generate
3. No codebase search, no self-critique

### Medium Mode

Balanced approach with root cause analysis.

```bash
pynext g page Dashboard --ai --thought-depth medium
```

What happens:
1. Generate code
2. If error: Identify error → Analyze why → Suggest fix → Generate
3. May search codebase for patterns

### Deep Mode (Default)

Full analysis with self-critique. Best for production code.

```bash
pynext g island DataTable --ai --thought-depth deep --verbose
```

What happens:
1. Generate code
2. If error:
   - Identify error
   - Analyze root cause
   - Search PyNext codebase for correct patterns
   - Form hypothesis
   - Self-critique the proposed fix
   - Generate only when confident

### Understanding Thought Output (--verbose)

When using `--verbose`, you'll see the AI's reasoning:

```
🤖 Generating page: products...

⚠️  Initial code has errors. Starting thought thread...

💭 Thought 1/5...
   Observation: SyntaxError: missing parentheses in call to 'div'
   Confidence: 85%
   🔍 Searching: ["PyNext div syntax", "element children"]

💭 Thought 2/5...
   Observation: Import error - Signal not imported
   Confidence: 95%
   ✓ Self-critique: Confident in fix

🔄 Generating improved code with context...

✅ Generated valid code after 2 thoughts!
```

---

## Validation Levels

### Syntax Validation

Just checks if the code compiles. Fastest but catches fewest issues.

```bash
pynext g component Card --ai --validation syntax
```

Catches:
- SyntaxError
- IndentationError

### Import Validation

Checks syntax plus validates PyNext imports.

```bash
pynext g component Card --ai --validation imports
```

Additional catches:
- Unknown PyNext modules
- Missing imports

### Full Validation (Default)

Comprehensive validation including PyNext patterns.

```bash
pynext g island Counter --ai --validation full
```

Additional catches:
- Missing decorators (@island, @action, etc.)
- Incorrect Signal usage
- React patterns accidentally used
- Common mistakes (class vs class_, input vs input_)

---

## CLI Reference

### Basic Flags

```bash
pynext g <type> <name> [options]
```

| Flag | Description |
|------|-------------|
| `--ai` | Enable AI-assisted generation |
| `-p, --prompt` | Direct prompt (skips interview) |
| `--api-key` | Anthropic API key (overrides env) |
| `-v, --verbose` | Show reasoning process |

### Model & Thought Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--model` | `claude-sonnet-4-20250514` | AI model to use |
| `--max-thoughts` | `5` | Max reasoning steps |
| `--thought-depth` | `deep` | shallow, medium, or deep |
| `--validation` | `full` | syntax, imports, or full |
| `--no-agent` | `false` | Disable agentic system |

### Examples

```bash
# Use a more powerful model
pynext g page complex-dashboard --ai --model claude-opus-4-20250514

# Quick generation with shallow thinking
pynext g component SimpleButton --ai --thought-depth shallow -p "Primary button"

# Maximum analysis for critical component
pynext g island PaymentForm --ai --max-thoughts 10 --thought-depth deep --verbose

# Legacy mode (no validation, just generate)
pynext g page test --ai --no-agent -p "Test page"
```

---

## Python API

### Basic Generation

```python
from pynext.generator.ai import generate_with_ai

code = generate_with_ai(
    generator_type="page",
    name="products",
    answers={"purpose": "Product listing", "data": "Product cards"},
)
```

### With Custom Configuration

```python
from pynext.generator.ai import generate_with_ai

code = generate_with_ai(
    generator_type="island",
    name="DataTable",
    answers={"purpose": "Sortable data table", "data": "User list"},
    model="claude-opus-4-20250514",
    max_thoughts=10,
    thought_depth="deep",
    validation_level="full",
    verbose=True,
)
```

### Using AIConfig

```python
from pynext.generator.config import AIConfig, ThoughtConfig
from pynext.generator.agent import GeneratorAgent

# Custom configuration
config = AIConfig(
    model="claude-opus-4-20250514",
    thought=ThoughtConfig(
        max_thoughts=10,
        thought_depth="deep",
        enable_codebase_search=True,
        enable_self_critique=True,
        confidence_threshold=0.9,
    ),
)

# Create agent
agent = GeneratorAgent(config)

# Generate (async)
import asyncio

code = asyncio.run(agent.generate(
    generator_type="page",
    name="products",
    answers={"description": "Product listing page"},
    verbose=True,
))
```

### Quick Generation

```python
from pynext.generator.ai import generate_quick

code = generate_quick(
    generator_type="component",
    name="ProductCard",
    description="Card showing product image, title, price, and add-to-cart button",
    model="claude-sonnet-4-20250514",
    verbose=True,
)
```

### Direct Validator Usage

```python
from pynext.generator.validator import CodeValidator, ValidationLevel

validator = CodeValidator(level=ValidationLevel.FULL)
result = validator.validate(code, generator_type="island")

if not result.valid:
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
    print(f"Suggestions: {result.suggestions}")
```

### Codebase Search

```python
from pynext.generator.search import CodebaseSearch

searcher = CodebaseSearch()

# Search for patterns
results = searcher.search("Signal state management")

# Get specific pattern example
signal_example = searcher.get_pattern("signals")
```

---

## Best Practices

### 1. Start with Verbose Mode

When debugging generation issues, always use `--verbose`:

```bash
pynext g page complex --ai --verbose
```

This shows exactly what the AI is thinking and helps identify issues.

### 2. Match Model to Complexity

| Use Case | Recommended Model |
|----------|-------------------|
| Simple components | claude-sonnet-4 (default) |
| Complex pages | claude-sonnet-4 |
| Critical/complex logic | claude-opus-4 |

### 3. Be Specific in Prompts

❌ Bad:
```bash
pynext g page users --ai -p "user page"
```

✅ Good:
```bash
pynext g page users --ai -p "User management page with table showing name, email, role. Add search filter, sort by columns, and edit/delete actions. Include pagination."
```

### 4. Use Deep Mode for Production

For production code, use deep mode to catch more issues:

```bash
pynext g island PaymentForm --ai --thought-depth deep --validation full
```

### 5. Review Generated Code

Even with validation, always review AI-generated code:
- Check business logic
- Verify security considerations
- Test edge cases

---

## Troubleshooting

### Generation Fails After Max Thoughts

The AI couldn't generate valid code after all attempts. Try:

1. Use `--verbose` to see the reasoning
2. Simplify your requirements
3. Increase `--max-thoughts`
4. Try a more powerful model (`--model claude-opus-4-20250514`)

### "API Key Required" Error

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Or pass directly:
```bash
pynext g page test --ai --api-key sk-ant-...
```

### "anthropic not installed" Error

```bash
pip install anthropic
```

### Slow Generation

Generation can be slow because:
1. Multiple API calls for thinking
2. Codebase search

Speed up with:
```bash
pynext g page test --ai --thought-depth shallow --max-thoughts 2
```

### Incorrect PyNext Patterns

If the AI generates incorrect patterns:
1. Use `--validation full` (default)
2. Enable codebase search: Set `PYNEXT_AI_CODEBASE_SEARCH=true`
3. Use deep mode for more thorough analysis

---

## Available Models

| Model | Best For |
|-------|----------|
| `claude-opus-4-20250514` | Complex logic, critical code |
| `claude-sonnet-4-20250514` | General purpose (default) |
| `claude-haiku-3-20240307` | Quick prototyping |

Set via CLI (`--model`), environment (`ANTHROPIC_MODEL`), or config file.

---

## Related Documentation

- [Generator CLI Reference](../getting-started/CLI.md)
- [Component Patterns](../tutorials/concepts/component-patterns.md)
- [PyNext HTML API](../core-concepts/HTML_API.md)
- [State Management](../core-concepts/STATE_MANAGEMENT.md)

