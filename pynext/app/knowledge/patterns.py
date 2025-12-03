"""
Pattern Library - Reusable PyNext code patterns.

Contains template code for common PyNext patterns:
- Pages (basic, with data, dynamic)
- Components (static, props, islands)
- State (signals, computed, effects)
- Data (models, API, actions)
- Auth (middleware, protected pages)
- Real-time (websockets, live queries)

Example:
    library = PatternLibrary()
    
    # Get pattern
    pattern = library.get("basic_page")
    print(pattern.code_template)
    
    # Get patterns for a feature
    patterns = library.get_patterns_for("authentication")
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


@dataclass
class Pattern:
    """
    A reusable PyNext code pattern.
    
    Attributes:
        name: Pattern identifier
        description: What this pattern does
        code_template: Template code with placeholders
        required_imports: Import statements needed
        related_patterns: Other patterns that work with this
        examples: Usage examples
        tags: Topics/categories
        placeholders: Dict of placeholder -> description
    """
    name: str
    description: str
    code_template: str
    required_imports: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    placeholders: Dict[str, str] = field(default_factory=dict)
    
    def render(self, **kwargs) -> str:
        """
        Render template with provided values.
        
        Args:
            **kwargs: Values for placeholders
        
        Returns:
            Rendered code
        """
        code = self.code_template
        for key, value in kwargs.items():
            placeholder = f"${{{key}}}"
            code = code.replace(placeholder, str(value))
        return code
    
    def get_imports(self) -> str:
        """Get import statements as string."""
        return "\n".join(self.required_imports)


class PatternLibrary:
    """
    Library of PyNext patterns for code generation.
    
    Contains all common patterns needed to build PyNext applications.
    """
    
    # ===========================================
    # Page Patterns
    # ===========================================
    
    BASIC_PAGE = Pattern(
        name="basic_page",
        description="Simple page with static content",
        code_template='''"""
${name} page.
"""
from pynext import div, h1, p

def page():
    """Render the ${name} page."""
    return div(class_="container mx-auto p-4")(
        h1(class_="text-3xl font-bold mb-4")("${title}"),
        p(class_="text-gray-600")("${description}"),
    )
''',
        required_imports=["from pynext import div, h1, p"],
        related_patterns=["page_with_data", "page_layout"],
        tags=["page", "routing"],
        placeholders={
            "name": "Page name",
            "title": "Page title",
            "description": "Page description",
        },
    )
    
    PAGE_WITH_DATA = Pattern(
        name="page_with_data",
        description="Page with async data fetching",
        code_template='''"""
${name} page with data loading.
"""
from pynext import div, h1, ul, li
from pynext.db import Table

async def get_data():
    """Fetch data for the page."""
    items = await ${model}.all()
    return {"items": items}

def page(data):
    """Render the ${name} page with data."""
    return div(class_="container mx-auto p-4")(
        h1(class_="text-2xl font-bold mb-4")("${title}"),
        ul(class_="space-y-2")(
            *[li(class_="p-2 border rounded")(item.${display_field}) 
              for item in data["items"]]
        ),
    )
''',
        required_imports=[
            "from pynext import div, h1, ul, li",
            "from pynext.db import Table",
        ],
        related_patterns=["database_model", "basic_page"],
        tags=["page", "data", "async"],
        placeholders={
            "name": "Page name",
            "title": "Page title",
            "model": "Database model class",
            "display_field": "Field to display",
        },
    )
    
    DYNAMIC_ROUTE_PAGE = Pattern(
        name="dynamic_route_page",
        description="Page with dynamic route parameter",
        code_template='''"""
${name} detail page - Dynamic route.
File: pages/${route_path}/[${param}].py
"""
from pynext import div, h1, p
from pynext.db import Table

async def get_data(params):
    """Fetch ${name} by ${param}."""
    ${param_var} = params.get("${param}")
    item = await ${model}.get(${param}=${param_var})
    return {"item": item}

def page(data):
    """Render ${name} detail."""
    item = data["item"]
    
    if not item:
        return div(class_="p-4")(
            h1(class_="text-xl")("Not Found"),
        )
    
    return div(class_="container mx-auto p-4")(
        h1(class_="text-2xl font-bold")(item.${title_field}),
        p(class_="text-gray-600 mt-2")(item.${description_field}),
    )
''',
        required_imports=[
            "from pynext import div, h1, p",
            "from pynext.db import Table",
        ],
        related_patterns=["page_with_data", "database_model"],
        tags=["page", "routing", "dynamic"],
        placeholders={
            "name": "Entity name",
            "route_path": "Route path",
            "param": "URL parameter name",
            "param_var": "Variable name for param",
            "model": "Database model",
            "title_field": "Field for title",
            "description_field": "Field for description",
        },
    )
    
    # ===========================================
    # Component Patterns
    # ===========================================
    
    STATIC_COMPONENT = Pattern(
        name="static_component",
        description="Simple reusable component",
        code_template='''"""
${name} component.
"""
from pynext import div, span

def ${component_name}(${props}):
    """
    ${description}
    
    Args:
        ${props_doc}
    """
    return div(class_="${container_class}")(
        ${content}
    )
''',
        required_imports=["from pynext import div, span"],
        related_patterns=["component_with_props", "island_component"],
        tags=["component"],
        placeholders={
            "name": "Component name",
            "component_name": "Function name (PascalCase)",
            "props": "Function parameters",
            "description": "Component description",
            "props_doc": "Args documentation",
            "container_class": "Container CSS classes",
            "content": "Component content",
        },
    )
    
    ISLAND_COMPONENT = Pattern(
        name="island_component",
        description="Interactive component with client-side state",
        code_template='''"""
${name} - Interactive island component.
"""
from pynext import div, button, span
from pynext import Signal
from pynext.islands import island

@island
def ${component_name}(${props}):
    """
    ${description}
    
    This component hydrates on the client for interactivity.
    """
    # State
    ${state_name} = Signal(${initial_state})
    
    # Handlers
    def ${handler_name}():
        ${handler_body}
    
    return div(class_="${container_class}")(
        ${content}
        button(
            class_="px-4 py-2 bg-blue-500 text-white rounded",
            on_click=${handler_name}
        )("${button_text}"),
        span(class_="ml-2")(${state_name}()),
    )
''',
        required_imports=[
            "from pynext import div, button, span",
            "from pynext import Signal",
            "from pynext.islands import island",
        ],
        related_patterns=["signal_state", "static_component"],
        tags=["island", "interactive", "state"],
        placeholders={
            "name": "Component name",
            "component_name": "Function name",
            "props": "Component props",
            "description": "Description",
            "state_name": "State variable name",
            "initial_state": "Initial state value",
            "handler_name": "Event handler name",
            "handler_body": "Handler logic",
            "container_class": "Container classes",
            "content": "Additional content",
            "button_text": "Button label",
        },
    )
    
    # ===========================================
    # State Patterns
    # ===========================================
    
    SIGNAL_STATE = Pattern(
        name="signal_state",
        description="Reactive state with Signal",
        code_template='''# Create reactive state
${name} = Signal(${initial_value})

# Read value (call like function)
current_value = ${name}()

# Update value
${name}.set(${new_value})

# Update based on previous value
${name}.set(${name}() + 1)
''',
        required_imports=["from pynext import Signal"],
        related_patterns=["computed_value", "effect_side_effect"],
        tags=["state", "signal", "reactive"],
        placeholders={
            "name": "State name",
            "initial_value": "Initial value",
            "new_value": "New value expression",
        },
    )
    
    COMPUTED_VALUE = Pattern(
        name="computed_value",
        description="Derived/computed value that auto-updates",
        code_template='''# Computed value - automatically updates when dependencies change
${name} = Computed(lambda: ${expression})

# Read computed value
value = ${name}()
''',
        required_imports=["from pynext import Computed"],
        related_patterns=["signal_state", "effect_side_effect"],
        tags=["state", "computed", "derived"],
        placeholders={
            "name": "Computed variable name",
            "expression": "Computation expression",
        },
    )
    
    EFFECT_SIDE_EFFECT = Pattern(
        name="effect_side_effect",
        description="Side effect that runs when dependencies change",
        code_template='''# Effect - runs when tracked values change
Effect(lambda: ${effect_body})

# Example: Log when count changes
Effect(lambda: print(f"Count is now: {count()}"))
''',
        required_imports=["from pynext import Effect"],
        related_patterns=["signal_state", "computed_value"],
        tags=["state", "effect", "side-effect"],
        placeholders={
            "effect_body": "Effect body (function to run)",
        },
    )
    
    # ===========================================
    # Data Patterns
    # ===========================================
    
    DATABASE_MODEL = Pattern(
        name="database_model",
        description="Database table model definition",
        code_template='''"""
${name} database model.
"""
from pynext.db import Table, Column, types

class ${model_name}(Table):
    """${description}"""
    
    id = Column(types.Integer, primary_key=True)
    ${fields}
    created_at = Column(types.DateTime, default="now()")
    updated_at = Column(types.DateTime, default="now()", on_update="now()")
''',
        required_imports=["from pynext.db import Table, Column, types"],
        related_patterns=["api_crud", "page_with_data"],
        tags=["database", "model", "table"],
        placeholders={
            "name": "Model name",
            "model_name": "Class name",
            "description": "Model description",
            "fields": "Field definitions",
        },
    )
    
    API_CRUD = Pattern(
        name="api_crud",
        description="CRUD API endpoints",
        code_template='''"""
${name} API endpoints.
"""
from pynext.api import api, Request, Response

@api
async def GET(request: Request):
    """List all ${name_plural} or get one by ID."""
    ${id_param} = request.query_params.get("id")
    
    if ${id_param}:
        item = await ${model}.get(id=int(${id_param}))
        return Response.json(item.to_dict() if item else None)
    
    items = await ${model}.all()
    return Response.json([item.to_dict() for item in items])

@api
async def POST(request: Request):
    """Create a new ${name}."""
    data = await request.json()
    item = await ${model}.create(**data)
    return Response.json(item.to_dict(), status=201)

@api
async def PUT(request: Request):
    """Update a ${name}."""
    data = await request.json()
    item_id = data.pop("id")
    await ${model}.update(id=item_id, **data)
    item = await ${model}.get(id=item_id)
    return Response.json(item.to_dict())

@api
async def DELETE(request: Request):
    """Delete a ${name}."""
    item_id = request.query_params.get("id")
    await ${model}.delete(id=int(item_id))
    return Response.json({"deleted": True})
''',
        required_imports=[
            "from pynext.api import api, Request, Response",
        ],
        related_patterns=["database_model", "server_action"],
        tags=["api", "crud", "rest"],
        placeholders={
            "name": "Resource name (singular)",
            "name_plural": "Resource name (plural)",
            "model": "Model class name",
            "id_param": "ID parameter variable",
        },
    )
    
    SERVER_ACTION = Pattern(
        name="server_action",
        description="Server action for form handling",
        code_template='''"""
${name} server action.
"""
from pynext.actions import action, ActionError

@action
async def ${action_name}(form_data: dict):
    """
    ${description}
    
    Args:
        form_data: Form submission data
    
    Returns:
        Result dict with success status
    
    Raises:
        ActionError: If validation fails
    """
    # Validate
    ${validation_field} = form_data.get("${validation_field}", "").strip()
    if not ${validation_field}:
        raise ActionError("${validation_field} is required", field="${validation_field}")
    
    # Process
    ${process_logic}
    
    return {"success": True, ${return_data}}
''',
        required_imports=["from pynext.actions import action, ActionError"],
        related_patterns=["form_component", "api_crud"],
        tags=["action", "form", "server"],
        placeholders={
            "name": "Action name",
            "action_name": "Function name",
            "description": "What the action does",
            "validation_field": "Field to validate",
            "process_logic": "Processing logic",
            "return_data": "Additional return data",
        },
    )
    
    # ===========================================
    # Auth Patterns
    # ===========================================
    
    AUTH_MIDDLEWARE = Pattern(
        name="auth_middleware",
        description="Authentication middleware",
        code_template='''"""
Authentication middleware.
"""
from pynext.middleware import middleware, redirect

@middleware(paths=["${protected_paths}"])
async def auth_middleware(request, next_handler):
    """
    Protect routes that require authentication.
    
    Redirects to login if not authenticated.
    """
    # Check for session/token
    session = request.cookies.get("session")
    
    if not session:
        return redirect("${login_path}")
    
    # Validate session
    user = await validate_session(session)
    if not user:
        return redirect("${login_path}")
    
    # Attach user to request
    request.user = user
    
    return await next_handler(request)

async def validate_session(session: str):
    """Validate session and return user."""
    # Implement session validation
    pass
''',
        required_imports=["from pynext.middleware import middleware, redirect"],
        related_patterns=["protected_page", "login_form"],
        tags=["auth", "middleware", "security"],
        placeholders={
            "protected_paths": "Paths to protect (e.g., /dashboard/*)",
            "login_path": "Login page path",
        },
    )
    
    LOGIN_FORM = Pattern(
        name="login_form",
        description="Login form with authentication",
        code_template='''"""
Login page and form.
"""
from pynext import div, h1, form, input_, button, p
from pynext import Signal
from pynext.islands import island
from pynext.actions import action, ActionError

@action
async def login_action(form_data: dict):
    """Handle login submission."""
    email = form_data.get("email", "").strip()
    password = form_data.get("password", "")
    
    if not email:
        raise ActionError("Email is required", field="email")
    if not password:
        raise ActionError("Password is required", field="password")
    
    # Validate credentials
    user = await authenticate(email, password)
    if not user:
        raise ActionError("Invalid credentials", field="email")
    
    # Create session
    session = await create_session(user)
    
    return {"success": True, "redirect": "${redirect_path}"}

@island
def LoginForm():
    """Login form component."""
    error = Signal("")
    loading = Signal(False)
    
    return div(class_="max-w-md mx-auto p-6")(
        h1(class_="text-2xl font-bold mb-4")("Login"),
        form(action=login_action, class_="space-y-4")(
            div()(
                input_(
                    type_="email",
                    name="email",
                    placeholder="Email",
                    class_="w-full p-2 border rounded",
                    required=True,
                ),
            ),
            div()(
                input_(
                    type_="password",
                    name="password",
                    placeholder="Password",
                    class_="w-full p-2 border rounded",
                    required=True,
                ),
            ),
            button(
                type_="submit",
                class_="w-full py-2 bg-blue-500 text-white rounded",
            )("Login"),
        ),
    )

def page():
    return LoginForm()
''',
        required_imports=[
            "from pynext import div, h1, form, input_, button, p",
            "from pynext import Signal",
            "from pynext.islands import island",
            "from pynext.actions import action, ActionError",
        ],
        related_patterns=["auth_middleware", "server_action"],
        tags=["auth", "form", "login"],
        placeholders={
            "redirect_path": "Path to redirect after login",
        },
    )
    
    # ===========================================
    # Layout Patterns
    # ===========================================
    
    APP_LAYOUT = Pattern(
        name="app_layout",
        description="Application layout with navigation",
        code_template='''"""
Application layout.
File: pages/layout.py
"""
from pynext import div, header, nav, main, footer, a

def layout(children):
    """
    Main application layout.
    
    Wraps all pages with header, navigation, and footer.
    """
    return div(class_="min-h-screen flex flex-col")(
        header(class_="bg-${header_bg} text-white")(
            nav(class_="container mx-auto p-4 flex items-center justify-between")(
                a(href="/", class_="text-xl font-bold")("${app_name}"),
                div(class_="flex gap-4")(
                    ${nav_links}
                ),
            ),
        ),
        main(class_="flex-1 container mx-auto p-4")(
            children,
        ),
        footer(class_="bg-gray-100 p-4 text-center text-gray-600")(
            "${footer_text}",
        ),
    )
''',
        required_imports=[
            "from pynext import div, header, nav, main, footer, a",
        ],
        related_patterns=["basic_page", "nested_layout"],
        tags=["layout", "navigation"],
        placeholders={
            "header_bg": "Header background color",
            "app_name": "Application name",
            "nav_links": "Navigation links",
            "footer_text": "Footer text",
        },
    )
    
    # ===========================================
    # Real-time Patterns
    # ===========================================
    
    WEBSOCKET_CONNECTION = Pattern(
        name="websocket_connection",
        description="WebSocket connection for real-time updates",
        code_template='''"""
Real-time updates with WebSocket.
"""
from pynext import div, ul, li
from pynext import Signal
from pynext.islands import island
from pynext.client import use_websocket

@island
def ${component_name}():
    """Real-time ${name} with WebSocket."""
    messages = Signal([])
    connected = Signal(False)
    
    # WebSocket connection
    ws = use_websocket(
        url="${ws_url}",
        on_message=lambda data: messages.set([*messages(), data]),
        on_open=lambda: connected.set(True),
        on_close=lambda: connected.set(False),
    )
    
    return div(class_="p-4")(
        div(class_="mb-2")(
            "Status: ",
            "Connected" if connected() else "Disconnected",
        ),
        ul(class_="space-y-2")(
            *[li(class_="p-2 bg-gray-100 rounded")(msg) 
              for msg in messages()]
        ),
    )
''',
        required_imports=[
            "from pynext import div, ul, li",
            "from pynext import Signal",
            "from pynext.islands import island",
            "from pynext.client import use_websocket",
        ],
        related_patterns=["live_query", "island_component"],
        tags=["realtime", "websocket"],
        placeholders={
            "component_name": "Component function name",
            "name": "Feature name",
            "ws_url": "WebSocket URL",
        },
    )
    
    LIVE_QUERY = Pattern(
        name="live_query",
        description="Live database query that auto-updates",
        code_template='''"""
Live query - automatically updates when data changes.
"""
from pynext import div, ul, li
from pynext.islands import island
from pynext.db.live import LiveQuery

@island
def ${component_name}():
    """Display ${name} with live updates."""
    # Live query - auto-refreshes when data changes
    items = ${model}.live()${query_chain}
    
    if items.loading():
        return div(class_="p-4")("Loading...")
    
    if items.error():
        return div(class_="p-4 text-red-500")(
            f"Error: {items.error()}"
        )
    
    return div(class_="p-4")(
        ul(class_="space-y-2")(
            *[li(class_="p-2 border rounded")(item.${display_field})
              for item in items()]
        ),
    )
''',
        required_imports=[
            "from pynext import div, ul, li",
            "from pynext.islands import island",
            "from pynext.db.live import LiveQuery",
        ],
        related_patterns=["websocket_connection", "database_model"],
        tags=["realtime", "database", "live"],
        placeholders={
            "component_name": "Component function name",
            "name": "Data name",
            "model": "Model class",
            "query_chain": "Query chain (e.g., .where(active=True))",
            "display_field": "Field to display",
        },
    )
    
    # ===========================================
    # Pattern Registry
    # ===========================================
    
    PATTERNS: Dict[str, Pattern] = {}
    
    def __init__(self):
        """Initialize pattern registry."""
        # Register all patterns
        self.PATTERNS = {
            # Pages
            "basic_page": self.BASIC_PAGE,
            "page_with_data": self.PAGE_WITH_DATA,
            "dynamic_route_page": self.DYNAMIC_ROUTE_PAGE,
            # Components
            "static_component": self.STATIC_COMPONENT,
            "island_component": self.ISLAND_COMPONENT,
            # State
            "signal_state": self.SIGNAL_STATE,
            "computed_value": self.COMPUTED_VALUE,
            "effect_side_effect": self.EFFECT_SIDE_EFFECT,
            # Data
            "database_model": self.DATABASE_MODEL,
            "api_crud": self.API_CRUD,
            "server_action": self.SERVER_ACTION,
            # Auth
            "auth_middleware": self.AUTH_MIDDLEWARE,
            "login_form": self.LOGIN_FORM,
            # Layout
            "app_layout": self.APP_LAYOUT,
            # Real-time
            "websocket_connection": self.WEBSOCKET_CONNECTION,
            "live_query": self.LIVE_QUERY,
        }
    
    def get(self, name: str) -> Optional[Pattern]:
        """Get a pattern by name."""
        return self.PATTERNS.get(name)
    
    def get_all(self) -> Dict[str, Pattern]:
        """Get all patterns."""
        return self.PATTERNS.copy()
    
    def get_by_tag(self, tag: str) -> List[Pattern]:
        """Get patterns by tag."""
        return [p for p in self.PATTERNS.values() if tag in p.tags]
    
    def get_patterns_for(self, feature: str) -> List[Pattern]:
        """
        Get relevant patterns for a feature description.
        
        Args:
            feature: Feature description
        
        Returns:
            List of applicable patterns
        """
        feature_lower = feature.lower()
        patterns = []
        
        # Keywords to pattern mapping
        keyword_patterns = {
            "page": ["basic_page", "page_with_data"],
            "data": ["page_with_data", "database_model"],
            "dynamic": ["dynamic_route_page"],
            "component": ["static_component", "island_component"],
            "interactive": ["island_component"],
            "island": ["island_component"],
            "state": ["signal_state", "computed_value"],
            "signal": ["signal_state"],
            "database": ["database_model"],
            "model": ["database_model"],
            "api": ["api_crud"],
            "crud": ["api_crud"],
            "action": ["server_action"],
            "form": ["server_action", "login_form"],
            "auth": ["auth_middleware", "login_form"],
            "login": ["login_form"],
            "layout": ["app_layout"],
            "navigation": ["app_layout"],
            "websocket": ["websocket_connection"],
            "realtime": ["websocket_connection", "live_query"],
            "live": ["live_query"],
        }
        
        matched = set()
        for keyword, pattern_names in keyword_patterns.items():
            if keyword in feature_lower:
                matched.update(pattern_names)
        
        for name in matched:
            if name in self.PATTERNS:
                patterns.append(self.PATTERNS[name])
        
        return patterns
    
    def compose_patterns(self, pattern_names: List[str]) -> str:
        """
        Compose multiple patterns into a single file.
        
        Args:
            pattern_names: List of pattern names to compose
        
        Returns:
            Combined code with deduped imports
        """
        imports = set()
        code_sections = []
        
        for name in pattern_names:
            pattern = self.get(name)
            if pattern:
                imports.update(pattern.required_imports)
                code_sections.append(f"# {pattern.description}\n{pattern.code_template}")
        
        # Combine
        result = "\n".join(sorted(imports))
        result += "\n\n"
        result += "\n\n".join(code_sections)
        
        return result

