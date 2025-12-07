"""
PyNext Database Relationships Package.

Provides bidirectional relationship support with automatic sync and loading strategies.

Design Philosophy:
- Simple API: One parameter (backref) enables bidirectional sync
- One parameter (lazy) controls loading strategy
- Fine-grained: Only affected relationships update (SolidJS principle)
- No magic: Explicit, traceable behavior that LLMs can follow
- AI-friendly: Easy to understand, extend, and debug

Usage:
    from pynext.db import Table, has_many, belongs_to, selectinload
    
    class User(Table):
        posts: List["Post"] = has_many("Post", backref="author", lazy="selectin")
        profile: Profile = has_one(Profile, lazy="joined")
    
    class Post(Table):
        author_id: int
        # author: User is auto-created via backref
    
    # Both sides sync automatically:
    user.posts.append(post)  # Also sets post.author = user
    
    # Query-level loading options:
    users = await User.select().options(
        selectinload("posts"),
    ).where(active=True)
"""

# Core relationship types and functions (from original relationships.py)
from pynext.db.relationships.core import (
    RelationshipType,
    RelationshipInfo,
    BelongsTo,
    HasMany,
    HasOne,
    ManyToMany,
    belongs_to,
    has_many,
    has_one,
    many_to_many,
    setup_relationships,
    detect_relationships,
    detect_reverse_relationships,
    process_backrefs,
)

# Backref configuration and sync
from pynext.db.relationships.backref import (
    BackrefConfig,
    BackrefRegistry,
    RelationshipSyncManager,
    get_backref_registry,
    get_sync_manager,
    reset_backref_registry,
    reset_sync_manager,
)

# Collections
from pynext.db.relationships.collections import (
    SyncedList,
)

# Many-to-Many
from pynext.db.relationships.m2m_collection import (
    ManyToManyCollection,
)
from pynext.db.relationships.m2m_dynamic import (
    DynamicManyToMany,
)
from pynext.db.relationships.junction import (
    JunctionConfig,
    JunctionTableFactory,
    JunctionManager,
    get_junction_factory,
    reset_junction_factory,
    create_junction_config,
    create_junction_with_extra,
)
from pynext.db.relationships.proxy import (
    AssociationProxy,
    AssociationProxyDescriptor,
)

# Association Proxy (Phase 7.9)
from pynext.db.relationships.association_proxy import (
    association_proxy,
    AttributeProxyDescriptor,
    ProxyCollection,
    proxy,
    attr_proxy,
)

# Loading strategies
from pynext.db.relationships.loading import (
    LoadStrategy,
    LoadOption,
    LazyLoadError,
    RelationshipLoader,
    JoinBuilder,
    get_loader,
    reset_loader,
)

# Loading option functions
from pynext.db.relationships.options import (
    joinedload,
    selectinload,
    subqueryload,
    raiseload,
    noload,
    lazyload,
    immediateload,
    eagerload,
    Load,
)

# Dynamic relationships
from pynext.db.relationships.dynamic import (
    DynamicRelationship,
    DynamicHasManyDescriptor,
)

# Cascade options
from pynext.db.relationships.cascade import (
    OnDeleteAction,
    CascadeOptions,
    CascadeResult,
    CascadeError,
    ProtectedDeleteError,
    OrphanDeleteError,
    CascadeManager,
    get_cascade_manager,
    reset_cascade_manager,
    cascade_options,
)

# Filter conditions (Phase 7.5)
from pynext.db.relationships.conditions import (
    Condition,
    eq,
    ne,
    gt,
    gte,
    lt,
    lte,
    like,
    ilike,
    not_like,
    is_in,
    not_in,
    is_null,
    # Aliases
    equals,
    not_equals,
    greater_than,
    greater_than_or_equal,
    less_than,
    less_than_or_equal,
    contains,
    normalize_condition,
    normalize_conditions,
)

# Filter class
from pynext.db.relationships.filter import (
    RelationshipFilter,
    parse_filter,
)

# Date/time helpers
from pynext.db.relationships.helpers import (
    days_ago,
    hours_ago,
    minutes_ago,
    seconds_ago,
    weeks_ago,
    months_ago,
    years_ago,
    days_from_now,
    hours_from_now,
    minutes_from_now,
    today,
    yesterday,
    tomorrow,
    start_of_today,
    end_of_today,
    start_of_week,
    start_of_month,
    start_of_year,
    now,
    utc_now,
)

# Tree/Self-Referential (Phase 7.6)
from pynext.db.relationships.tree import (
    TreeMixin,
)
from pynext.db.relationships.tree_query import (
    TreeQueryBuilder,
)

# Relationship Hooks (Phase 7.8)
from pynext.db.relationships.hooks import (
    HookType,
    HookConfig,
    HookRegistry,
    on_append,
    on_remove,
    on_set,
    before_delete,
    get_hook_registry,
    reset_hook_registries,
    discover_hooks,
    has_hooks,
    get_hooks_for_relationship,
    fire_hooks,
)
from pynext.db.relationships.hook_executor import (
    HookExecutor,
    get_hook_executor,
    reset_hook_executor,
    set_hook_executor,
    fire_on_append,
    fire_on_remove,
    fire_on_set,
    fire_before_delete,
)

# Association Proxy (Phase 7.9)
from pynext.db.relationships.association_proxy import (
    association_proxy,
    AttributeProxyDescriptor,
    ProxyCollection,
    proxy,
    attr_proxy,
)

# Ordering (Phase 7.10)
from pynext.db.relationships.ordering import (
    OrderSpec,
    OrderingConfig,
    parse_order_by,
    parse_order_spec,
    build_order_clause,
    build_order_columns,
    validate_order_by,
    normalize_order_by,
    asc,
    desc,
    sort_items,
)

__all__ = [
    # Core types
    "RelationshipType",
    "RelationshipInfo",
    "BelongsTo",
    "HasMany",
    "HasOne",
    "ManyToMany",
    "belongs_to",
    "has_many",
    "has_one",
    "many_to_many",
    "setup_relationships",
    "detect_relationships",
    "detect_reverse_relationships",
    "process_backrefs",
    # Backref configuration
    "BackrefConfig",
    "BackrefRegistry",
    "RelationshipSyncManager",
    "get_backref_registry",
    "get_sync_manager",
    "reset_backref_registry",
    "reset_sync_manager",
    # Collections
    "SyncedList",
    "ManyToManyCollection",
    # Many-to-Many
    "JunctionConfig",
    "JunctionTableFactory",
    "JunctionManager",
    "get_junction_factory",
    "reset_junction_factory",
    "create_junction_config",
    "create_junction_with_extra",
    "DynamicManyToMany",
    "AssociationProxy",
    "AssociationProxyDescriptor",
    # Loading strategies
    "LoadStrategy",
    "LoadOption",
    "LazyLoadError",
    "RelationshipLoader",
    "JoinBuilder",
    "get_loader",
    "reset_loader",
    # Loading option functions
    "joinedload",
    "selectinload",
    "subqueryload",
    "raiseload",
    "noload",
    "lazyload",
    "immediateload",
    "eagerload",
    "Load",
    # Dynamic relationships
    "DynamicRelationship",
    "DynamicHasManyDescriptor",
    # Cascade options
    "OnDeleteAction",
    "CascadeOptions",
    "CascadeResult",
    "CascadeError",
    "ProtectedDeleteError",
    "OrphanDeleteError",
    "CascadeManager",
    "get_cascade_manager",
    "reset_cascade_manager",
    "cascade_options",
    # Filter conditions (Phase 7.5)
    "Condition",
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "like",
    "ilike",
    "not_like",
    "is_in",
    "not_in",
    "is_null",
    "equals",
    "not_equals",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "contains",
    "normalize_condition",
    "normalize_conditions",
    # Filter class
    "RelationshipFilter",
    "parse_filter",
    # Date/time helpers
    "days_ago",
    "hours_ago",
    "minutes_ago",
    "seconds_ago",
    "weeks_ago",
    "months_ago",
    "years_ago",
    "days_from_now",
    "hours_from_now",
    "minutes_from_now",
    "today",
    "yesterday",
    "tomorrow",
    "start_of_today",
    "end_of_today",
    "start_of_week",
    "start_of_month",
    "start_of_year",
    "now",
    "utc_now",
    # Tree/Self-Referential (Phase 7.6)
    "TreeMixin",
    "TreeQueryBuilder",
    # Relationship Hooks (Phase 7.8)
    "HookType",
    "HookConfig",
    "HookRegistry",
    "on_append",
    "on_remove",
    "on_set",
    "before_delete",
    "get_hook_registry",
    "reset_hook_registries",
    "discover_hooks",
    "has_hooks",
    "get_hooks_for_relationship",
    "fire_hooks",
    "HookExecutor",
    "get_hook_executor",
    "reset_hook_executor",
    "set_hook_executor",
    "fire_on_append",
    "fire_on_remove",
    "fire_on_set",
    "fire_before_delete",
    # Association Proxy (Phase 7.9)
    "association_proxy",
    "AttributeProxyDescriptor",
    "ProxyCollection",
    "proxy",
    "attr_proxy",
    # Ordering (Phase 7.10)
    "OrderSpec",
    "OrderingConfig",
    "parse_order_by",
    "parse_order_spec",
    "build_order_clause",
    "build_order_columns",
    "validate_order_by",
    "normalize_order_by",
    "asc",
    "desc",
    "sort_items",
]

