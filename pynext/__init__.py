"""
PyNext - A Python alternative to Next.js with SolidJS-inspired reactivity.

This framework provides:
- File-based routing with layouts
- Fine-grained reactivity via signals
- Server actions for Python package execution
- NPM package integration
- React component support via Preact (~4KB runtime)
- Metadata API for SEO
- API routes for REST endpoints
- Image optimization (build-time, zero JS)
- Static Site Generation (SSG)
- Incremental Static Regeneration (ISR)
- Edge Middleware
- Internationalization (i18n)
- Font optimization (zero JS, build-time)
- Script optimization (native loading)
- Partial Prerendering (PPR)
- Parallel Routes (@folder convention)
- Intercepting Routes ((..) convention)
- Draft Mode (signal-based preview)
"""

__version__ = "0.1.0"

# Core reactive primitives
from pynext.core.signals import Signal, Effect, Memo, Store, Computed, batch
from pynext.core.resource import Resource, create_resource, ResourceState, get_resource_registry
from pynext.core.suspense import Suspense, Show, Switch, Match, ErrorBoundary

# Image Optimization
from pynext.core.image import (
    Image,
    ImageConfig,
    ImageLayout,
    ImageLoading,
    ImageFormat,
    ResponsiveImage,
    FillImage,
    PriorityImage,
    Avatar,
    configure_images,
    get_image_registry,
)

# Static Site Generation
from pynext.core.static import (
    static_page,
    static_props,
    static_paths,
    StaticPageConfig,
    GenerationMode,
    StaticPath,
    get_static_pages,
    analyze_page,
)

# Incremental Static Regeneration
from pynext.core.isr import (
    revalidate,
    revalidate_path,
    revalidate_tag,
    revalidate_component,
    RevalidateConfig,
    InvalidationScope,
    get_isr_cache,
    init_isr_cache,
)

# i18n
from pynext.i18n import (
    t,
    use_locale,
    get_locale,
    set_locale,
    LocaleConfig,
    LocaleProvider,
    format_number,
    format_date,
    format_currency,
    load_translations,
    register_translations,
)

# Islands (Selective Hydration)
from pynext.core.island import (
    island,
    static,
    HydrationStrategy,
    IslandBoundary,
    is_interactive,
    collect_islands,
    get_island_hydration_data,
    generate_island_script,
)

# Lazy Loading (Code Splitting)
from pynext.core.lazy import (
    lazy,
    lazy_route,
    LazyComponent,
    LazyBoundary,
    LoadingState,
    PrefetchStrategy,
    import_component,
    prefetch_link,
    get_lazy_registry,
)

# Transitions & Navigation
from pynext.core.transitions import (
    transition,
    Link,
    TransitionType,
    TransitionConfig,
    TransitionManager,
    NavigationState,
    PageTransition,
    get_transition_manager,
    get_transition_css,
    get_transition_style_tag,
    navigate_script,
    back_script,
    forward_script,
)

# Component decorators
from pynext.core.component import (
    component, 
    page, 
    layout, 
    loading, 
    error, 
    not_found,
    Show,
    For,
)

# Metadata API
from pynext.core.metadata import (
    Metadata,
    OpenGraph,
    Twitter,
    Icons,
    Alternates,
    generate_metadata,
)

# API Routes
from pynext.core.api_route import (
    api_route,
    JSONResponse,
    Response,
    RedirectResponse,
    HTMLResponse,
)

# React integration
from pynext.react import ReactComponent, ReactIsland

# HTML element builders
from pynext.core.html import (
    # Document structure
    html, head, body, title, meta, link, script, style,
    # Layout
    div, span, section, article, header, footer, nav, aside, main,
    # Text
    h1, h2, h3, h4, h5, h6, p, a, strong, em, code, pre, blockquote,
    # Lists
    ul, ol, li, dl, dt, dd,
    # Forms
    form, input_, textarea, button, select, option, label, fieldset, legend,
    # Tables
    table, thead, tbody, tfoot, tr, th, td,
    # Media
    img, video, audio, source, canvas, svg,
    # Semantic
    figure, figcaption, details, summary, time, mark, progress,
    # Interactive
    dialog, menu,
    # Generic
    element,
    # Fragment for grouping without wrapper
    Fragment,
    # Raw HTML
    raw_html,
)

# Server actions
from pynext.server.actions import server_action

# Router utilities
from pynext.router.file_router import get_params, get_query

# Context utilities
from pynext.core.context import RenderContext, get_context

# Middleware
from pynext.middleware import (
    middleware,
    MiddlewareConfig,
    MiddlewareContext,
    NextResponse,
    redirect,
    rewrite,
    next_response,
)

# Font Optimization
from pynext.core.font import (
    Font,
    GoogleFont,
    LocalFont,
    FontConfig,
    FontDisplay,
    FontStyle,
    FontWeight,
    get_font_registry,
    get_font_style_tag,
    get_font_preload_links,
)

# Script Optimization
from pynext.core.script import (
    Script,
    InlineScript,
    ModuleScript,
    AnalyticsScript,
    WorkerScript,
    ImportMap,
    ScriptStrategy,
    get_head_scripts,
    get_body_scripts,
    clear_scripts,
)

# Partial Prerendering (PPR)
from pynext.core.ppr import (
    partial_prerender,
    static_part,
    dynamic_part,
    StaticShell,
    DynamicHole,
    PPRMode,
    ComponentType,
    get_ppr_context,
    create_ppr_context,
    analyze_component,
)

# Parallel Routes
from pynext.core.slot import (
    Slot,
    SlotGroup,
    get_slot_context,
    create_slot_context,
    set_slot_content,
    sidebar_slot,
    main_slot,
    modal_slot,
)

# Intercepting Routes
from pynext.core.modal import (
    Modal,
    ModalPortal,
    modal,
    photo_modal,
    form_modal,
)

# Draft Mode
from pynext.core.draft import (
    use_draft,
    is_draft_mode,
    enable_draft,
    disable_draft,
    draft_content,
    draft_only,
    published_only,
    DraftSwitch,
    DraftBanner,
    DraftOverlay,
)

# Error Types and Pages
from pynext.core.errors import (
    PyNextError,
    UnauthorizedError,
    ForbiddenError,
    NotFoundError,
    ServerError,
    BadRequestError,
    unauthorized,
    forbidden,
    not_found as raise_not_found,  # Renamed to avoid conflict with @not_found decorator
    bad_request,
    server_error,
    unauthorized_page,
    forbidden_page,
    not_found_page,
    server_error_page,
)

# Template (Layouts that remount)
from pynext.core.template import (
    template,
    Template,
    TemplateConfig,
    TransitionType as TemplateTransitionType,
    fade_template,
    slide_template,
    scale_template,
    static_template,
)

# Path Resolution
from pynext.core.paths import (
    ProjectPaths,
    resolve_paths,
    detect_structure,
    get_watch_dirs,
    ensure_structure,
    find_project_root,
    validate_structure,
    get_page_url,
)

# Route Groups
from pynext.router.groups import (
    is_route_group,
    strip_groups,
    get_group_name,
    get_groups_in_path,
    RouteGroup,
    GroupRegistry,
    scan_groups,
)

# SEO (Sitemap & Robots)
from pynext.seo import (
    SitemapEntry,
    SitemapConfig,
    sitemap,
    get_sitemap_config,
    has_sitemap_config,
    SitemapGenerator,
    RobotsRule,
    RobotsConfig,
    robots_allow_all,
    robots_disallow_all,
    RobotsGenerator,
)

# Route Configuration
from pynext.core.route_config import (
    RouteConfig,
    Dynamic,
    Cache,
    Runtime,
    route_config,
    get_route_config,
    has_route_config,
    static_route,
    dynamic_route,
    edge_route,
    cached_route,
    no_cache_route,
    get_effective_config,
    register_path_config,
    get_config_by_path,
)

# Environment Variables
from pynext.env_module import env, Env
from pynext.env import (
    load_env_files,
    parse_env_file,
    expand_variables,
    get_env_files_info,
    Var,
    ValidationError,
    ValidationResult,
    EnvSchema,
    EnvConfig,
    load_schema,
    get_public_vars,
    generate_inline_script,
    generate_runtime_script,
    inline_env_in_js,
    get_client_env_accessor,
)

# Client-Side Primitives
from pynext.core.client import (
    on_keydown,
    on_key_sequence,
    register_shortcut,
    unregister_shortcut,
    use_storage,
    use_ref,
    client_effect,
    use_theme,
    get_client_hydration_data,
    # Browser APIs
    use_event_source,
    SSEHandle,
    use_visibility,
    VisibilitySignal,
    use_online,
    OnlineSignal,
)

__all__ = [
    # Version
    "__version__",
    # Signals
    "Signal",
    "Effect", 
    "Memo",
    "Store",
    "Computed",
    "batch",
    # Resource (async data)
    "Resource",
    "create_resource",
    "ResourceState",
    "get_resource_registry",
    # Suspense & Control Flow
    "Suspense",
    "Show",
    "Switch",
    "Match",
    "ErrorBoundary",
    # Image Optimization
    "Image",
    "ImageConfig",
    "ImageLayout",
    "ImageLoading",
    "ImageFormat",
    "ResponsiveImage",
    "FillImage",
    "PriorityImage",
    "Avatar",
    "configure_images",
    "get_image_registry",
    # Static Site Generation
    "static_page",
    "static_props",
    "static_paths",
    "StaticPageConfig",
    "GenerationMode",
    "StaticPath",
    "get_static_pages",
    "analyze_page",
    # ISR
    "revalidate",
    "revalidate_path",
    "revalidate_tag",
    "revalidate_component",
    "RevalidateConfig",
    "InvalidationScope",
    "get_isr_cache",
    "init_isr_cache",
    # i18n
    "t",
    "use_locale",
    "get_locale",
    "set_locale",
    "LocaleConfig",
    "LocaleProvider",
    "format_number",
    "format_date",
    "format_currency",
    "load_translations",
    "register_translations",
    # Middleware
    "middleware",
    "MiddlewareConfig",
    "MiddlewareContext",
    "NextResponse",
    "redirect",
    "rewrite",
    "next_response",
    # Islands (Selective Hydration)
    "island",
    "static",
    "HydrationStrategy",
    "IslandBoundary",
    "is_interactive",
    "collect_islands",
    "get_island_hydration_data",
    "generate_island_script",
    # Lazy Loading (Code Splitting)
    "lazy",
    "lazy_route",
    "LazyComponent",
    "LazyBoundary",
    "LoadingState",
    "PrefetchStrategy",
    "import_component",
    "prefetch_link",
    "get_lazy_registry",
    # Transitions & Navigation
    "transition",
    "Link",
    "TransitionType",
    "TransitionConfig",
    "TransitionManager",
    "NavigationState",
    "PageTransition",
    "get_transition_manager",
    "get_transition_css",
    "get_transition_style_tag",
    "navigate_script",
    "back_script",
    "forward_script",
    # Components
    "component",
    "page",
    "layout",
    "loading",
    "error",
    "not_found",
    "Show",
    "For",
    # Metadata
    "Metadata",
    "OpenGraph",
    "Twitter",
    "Icons",
    "Alternates",
    "generate_metadata",
    # API Routes
    "api_route",
    "JSONResponse",
    "Response",
    "RedirectResponse",
    "HTMLResponse",
    # React
    "ReactComponent",
    "ReactIsland",
    # HTML elements
    "html", "head", "body", "title", "meta", "link", "script", "style",
    "div", "span", "section", "article", "header", "footer", "nav", "aside", "main",
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "strong", "em", "code", "pre", "blockquote",
    "ul", "ol", "li", "dl", "dt", "dd",
    "form", "input_", "textarea", "button", "select", "option", "label", "fieldset", "legend",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td",
    "img", "video", "audio", "source", "canvas", "svg",
    "figure", "figcaption", "details", "summary", "time", "mark", "progress",
    "dialog", "menu",
    "element",
    "Fragment",
    "raw_html",
    # Server
    "server_action",
    # Router
    "get_params",
    "get_query",
    # Context
    "RenderContext",
    "get_context",
    # Font Optimization
    "Font",
    "GoogleFont",
    "LocalFont",
    "FontConfig",
    "FontDisplay",
    "FontStyle",
    "FontWeight",
    "get_font_registry",
    "get_font_style_tag",
    "get_font_preload_links",
    # Script Optimization
    "Script",
    "InlineScript",
    "ModuleScript",
    "AnalyticsScript",
    "WorkerScript",
    "ImportMap",
    "ScriptStrategy",
    "get_head_scripts",
    "get_body_scripts",
    "clear_scripts",
    # Partial Prerendering (PPR)
    "partial_prerender",
    "static_part",
    "dynamic_part",
    "StaticShell",
    "DynamicHole",
    "PPRMode",
    "ComponentType",
    "get_ppr_context",
    "create_ppr_context",
    "analyze_component",
    # Parallel Routes (Slots)
    "Slot",
    "SlotGroup",
    "get_slot_context",
    "create_slot_context",
    "set_slot_content",
    "sidebar_slot",
    "main_slot",
    "modal_slot",
    # Intercepting Routes (Modal)
    "Modal",
    "ModalPortal",
    "modal",
    "photo_modal",
    "form_modal",
    # Draft Mode
    "use_draft",
    "is_draft_mode",
    "enable_draft",
    "disable_draft",
    "draft_content",
    "draft_only",
    "published_only",
    "DraftSwitch",
    "DraftBanner",
    "DraftOverlay",
    # Client-Side Primitives
    "on_keydown",
    "on_key_sequence",
    "register_shortcut",
    "unregister_shortcut",
    "use_storage",
    "use_ref",
    "client_effect",
    "use_theme",
    "get_client_hydration_data",
    # Browser APIs
    "use_event_source",
    "SSEHandle",
    "use_visibility",
    "VisibilitySignal",
    "use_online",
    "OnlineSignal",
    # Error Types and Pages
    "PyNextError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ServerError",
    "BadRequestError",
    "unauthorized",
    "forbidden",
    "raise_not_found",  # Renamed to avoid conflict with @not_found decorator
    "bad_request",
    "server_error",
    "unauthorized_page",
    "forbidden_page",
    "not_found_page",
    "server_error_page",
    # Template
    "template",
    "Template",
    "TemplateConfig",
    "TemplateTransitionType",
    "fade_template",
    "slide_template",
    "scale_template",
    "static_template",
    # Path Resolution
    "ProjectPaths",
    "resolve_paths",
    "detect_structure",
    "get_watch_dirs",
    "ensure_structure",
    "find_project_root",
    "validate_structure",
    "get_page_url",
    # Route Groups
    "is_route_group",
    "strip_groups",
    "get_group_name",
    "get_groups_in_path",
    "RouteGroup",
    "GroupRegistry",
    "scan_groups",
    # SEO (Sitemap & Robots)
    "SitemapEntry",
    "SitemapConfig",
    "sitemap",
    "get_sitemap_config",
    "has_sitemap_config",
    "SitemapGenerator",
    "RobotsRule",
    "RobotsConfig",
    "robots_allow_all",
    "robots_disallow_all",
    "RobotsGenerator",
    # Route Configuration
    "RouteConfig",
    "Dynamic",
    "Cache",
    "Runtime",
    "route_config",
    "get_route_config",
    "has_route_config",
    "static_route",
    "dynamic_route",
    "edge_route",
    "cached_route",
    "no_cache_route",
    "get_effective_config",
    "register_path_config",
    "get_config_by_path",
    # Environment Variables
    "env",
    "Env",
    "load_env_files",
    "parse_env_file",
    "expand_variables",
    "get_env_files_info",
    "Var",
    "ValidationError",
    "ValidationResult",
    "EnvSchema",
    "EnvConfig",
    "load_schema",
    "get_public_vars",
    "generate_inline_script",
    "generate_runtime_script",
    "inline_env_in_js",
    "get_client_env_accessor",
]

