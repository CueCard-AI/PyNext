"""
Interactive prompts for generator.

Simple, clear prompts. No complex TUI.
Guides users through options step by step.

Why Prompts?
    - Better UX for new users
    - Reduces mistakes
    - Captures intent, not just config
"""

from typing import Dict, Callable, Optional


# ============================================
# Prompt Definitions
# ============================================

def prompt_page(name: str) -> Dict:
    """
    Prompt for page options.
    
    Returns:
        Dict with template variables
    """
    print(f"\n📄 Creating page: {name}\n")
    
    props = {}
    
    # Dynamic route?
    is_dynamic = _ask_yes_no("  Is this a dynamic route? (e.g., [id])", default=False)
    if is_dynamic:
        param_name = _ask_input("  Parameter name", default="id")
        props["is_dynamic"] = True
        props["param_name"] = param_name
    
    # With data fetching?
    has_data = _ask_yes_no("  Fetch data on server? (async get_data)", default=True)
    props["has_data"] = has_data
    
    # With metadata?
    has_metadata = _ask_yes_no("  Include SEO metadata?", default=True)
    props["has_metadata"] = has_metadata
    
    return props


def prompt_component(name: str) -> Dict:
    """
    Prompt for component options.
    """
    print(f"\n🧩 Creating component: {name}\n")
    
    props = {}
    
    # What kind of component?
    is_interactive = _ask_yes_no("  Does it need client-side interactivity?", default=False)
    if is_interactive:
        print("  → Consider using 'pynext g island' instead for interactive components")
    props["is_interactive"] = is_interactive
    
    # Has variants?
    has_variants = _ask_yes_no("  Does it have variants? (e.g., sizes, colors)", default=True)
    props["has_variants"] = has_variants
    
    # Accepts children?
    accepts_children = _ask_yes_no("  Can it wrap other content?", default=False)
    props["accepts_children"] = accepts_children
    
    return props


def prompt_island(name: str) -> Dict:
    """
    Prompt for island options.
    """
    print(f"\n🏝️ Creating island: {name}\n")
    
    props = {}
    
    # What state does it manage?
    print("  What state will it manage?")
    print("    a) Counter/number")
    print("    b) Toggle/boolean")
    print("    c) Form data")
    print("    d) Custom/complex")
    
    state_type = _ask_choice("  Choice", ["a", "b", "c", "d"], default="d")
    props["state_type"] = {
        "a": "counter",
        "b": "toggle",
        "c": "form",
        "d": "custom",
    }[state_type]
    
    # Has effects?
    has_effects = _ask_yes_no("  Does it have side effects? (API calls, storage)", default=False)
    props["has_effects"] = has_effects
    
    return props


def prompt_api(name: str) -> Dict:
    """
    Prompt for API route options.
    """
    print(f"\n🔌 Creating API route: {name}\n")
    
    props = {}
    
    # HTTP methods
    print("  Which HTTP methods? (comma-separated)")
    print("    GET, POST, PUT, DELETE, PATCH")
    
    methods_input = _ask_input("  Methods", default="GET, POST")
    props["methods"] = [m.strip().upper() for m in methods_input.split(",")]
    
    # Authentication required?
    needs_auth = _ask_yes_no("  Requires authentication?", default=False)
    props["needs_auth"] = needs_auth
    
    return props


def prompt_layout(name: str) -> Dict:
    """
    Prompt for layout options.
    """
    print(f"\n📐 Creating layout: {name}\n")
    
    props = {}
    
    # Has navigation?
    has_nav = _ask_yes_no("  Include navigation bar?", default=True)
    props["has_nav"] = has_nav
    
    # Has footer?
    has_footer = _ask_yes_no("  Include footer?", default=True)
    props["has_footer"] = has_footer
    
    # Has sidebar?
    has_sidebar = _ask_yes_no("  Include sidebar?", default=False)
    props["has_sidebar"] = has_sidebar
    
    return props


def prompt_template(name: str) -> Dict:
    """
    Prompt for template options.
    """
    print(f"\n🎭 Creating template: {name}\n")
    
    props = {}
    
    # Animation type
    print("  Enter/exit animation?")
    print("    a) Fade")
    print("    b) Slide")
    print("    c) None")
    
    animation = _ask_choice("  Choice", ["a", "b", "c"], default="a")
    props["animation"] = {
        "a": "fade",
        "b": "slide",
        "c": "none",
    }[animation]
    
    return props


def prompt_loading(name: str) -> Dict:
    """
    Prompt for loading state options.
    """
    print(f"\n⏳ Creating loading state: {name}\n")
    
    props = {}
    
    # Skeleton type
    print("  Loading skeleton style?")
    print("    a) Text skeleton (lines)")
    print("    b) Card skeleton")
    print("    c) Table skeleton")
    print("    d) Simple spinner")
    
    skeleton_type = _ask_choice("  Choice", ["a", "b", "c", "d"], default="a")
    props["skeleton_type"] = {
        "a": "text",
        "b": "card",
        "c": "table",
        "d": "spinner",
    }[skeleton_type]
    
    return props


def prompt_error(name: str) -> Dict:
    """
    Prompt for error boundary options.
    """
    print(f"\n❌ Creating error boundary: {name}\n")
    
    props = {}
    
    # Show stack trace in dev?
    show_stack = _ask_yes_no("  Show stack trace in development?", default=True)
    props["show_stack"] = show_stack
    
    # Has retry button?
    has_retry = _ask_yes_no("  Include retry button?", default=True)
    props["has_retry"] = has_retry
    
    return props


def prompt_middleware(name: str) -> Dict:
    """
    Prompt for middleware options.
    """
    print(f"\n🔒 Creating middleware\n")
    
    props = {}
    
    # What does it do?
    print("  Primary purpose?")
    print("    a) Authentication check")
    print("    b) Logging")
    print("    c) Rate limiting")
    print("    d) Custom headers")
    print("    e) General purpose")
    
    purpose = _ask_choice("  Choice", ["a", "b", "c", "d", "e"], default="a")
    props["purpose"] = {
        "a": "auth",
        "b": "logging",
        "c": "rate_limit",
        "d": "headers",
        "e": "general",
    }[purpose]
    
    # Route matcher
    matcher = _ask_input("  Route pattern to match", default="/(.*)")
    props["matcher"] = matcher
    
    return props


def prompt_action(name: str) -> Dict:
    """
    Prompt for server action options.
    """
    print(f"\n⚡ Creating server action: {name}\n")
    
    props = {}
    
    # What does it do?
    print("  Action type?")
    print("    a) Create (form submission)")
    print("    b) Update")
    print("    c) Delete")
    print("    d) Custom mutation")
    
    action_type = _ask_choice("  Choice", ["a", "b", "c", "d"], default="a")
    props["action_type"] = {
        "a": "create",
        "b": "update",
        "c": "delete",
        "d": "custom",
    }[action_type]
    
    # Needs validation?
    needs_validation = _ask_yes_no("  Include input validation?", default=True)
    props["needs_validation"] = needs_validation
    
    return props


def prompt_hook(name: str) -> Dict:
    """
    Prompt for hook options.
    """
    print(f"\n🪝 Creating hook: {name}\n")
    
    props = {}
    
    # Hook type
    print("  Hook type?")
    print("    a) State (like useState)")
    print("    b) Toggle (boolean state)")
    print("    c) Counter (number with inc/dec)")
    print("    d) Fetch (data fetching)")
    print("    e) Custom")
    
    hook_type = _ask_choice("  Choice", ["a", "b", "c", "d", "e"], default="a")
    props["hook_type"] = {
        "a": "state",
        "b": "toggle",
        "c": "counter",
        "d": "fetch",
        "e": "custom",
    }[hook_type]
    
    return props


# ============================================
# Prompt Registry
# ============================================

PROMPTS: Dict[str, Callable[[str], Dict]] = {
    "page": prompt_page,
    "component": prompt_component,
    "island": prompt_island,
    "api": prompt_api,
    "layout": prompt_layout,
    "template": prompt_template,
    "loading": prompt_loading,
    "error": prompt_error,
    "middleware": prompt_middleware,
    "action": prompt_action,
    "hook": prompt_hook,
}


def prompt_for_type(generator_type: str, name: str) -> Dict:
    """
    Run prompts for a generator type.
    
    Args:
        generator_type: Type of generator
        name: Component name
    
    Returns:
        Dict with gathered options
    
    Example:
        props = prompt_for_type("page", "blog")
    """
    if generator_type not in PROMPTS:
        return {}
    
    return PROMPTS[generator_type](name)


# ============================================
# Helper Functions
# ============================================

def _ask_yes_no(question: str, default: bool = True) -> bool:
    """
    Ask a yes/no question.
    
    Args:
        question: Question to ask
        default: Default value if user presses Enter
    
    Returns:
        Boolean answer
    """
    default_str = "Y/n" if default else "y/N"
    answer = input(f"{question} [{default_str}]: ").strip().lower()
    
    if not answer:
        return default
    
    return answer in ("y", "yes", "true", "1")


def _ask_input(question: str, default: str = "") -> str:
    """
    Ask for text input.
    
    Args:
        question: Question to ask
        default: Default value
    
    Returns:
        User input or default
    """
    if default:
        answer = input(f"{question} [{default}]: ").strip()
        return answer if answer else default
    else:
        return input(f"{question}: ").strip()


def _ask_choice(question: str, choices: list, default: str = "") -> str:
    """
    Ask for a choice from options.
    
    Args:
        question: Question to ask
        choices: List of valid choices
        default: Default choice
    
    Returns:
        Selected choice
    """
    while True:
        if default:
            answer = input(f"{question} [{default}]: ").strip().lower()
            if not answer:
                return default
        else:
            answer = input(f"{question}: ").strip().lower()
        
        if answer in choices:
            return answer
        
        print(f"  Invalid choice. Options: {', '.join(choices)}")

