"""
PyNext Polymorphic Relationships.

Provides polymorphic inheritance patterns and generic foreign keys
that are dramatically simpler than SQLAlchemy or Django.

Features:
- @polymorphic decorator for inheritance hierarchies
- Single Table Inheritance (STI)
- Joined Table Inheritance
- Concrete Table Inheritance
- Generic Foreign Keys with Union types

Quick Start:
    from pynext.db import Table
    from pynext.db.polymorphic import polymorphic, generic_fk
    from typing import Union
    
    # Single Table Inheritance
    @polymorphic("type")
    class Content(Table):
        title: str
    
    @polymorphic.subtype("article")
    class Article(Content):
        body: str
    
    @polymorphic.subtype("video")
    class Video(Content):
        url: str
    
    # Automatic type inference
    contents = await Content.all()  # [Article(...), Video(...)]
    
    # Generic Foreign Keys
    class Comment(Table):
        content: str
        target: Union[Article, Video] = generic_fk()
    
    # Set target
    comment = await Comment.create(content="Great!", target=article)
    
    # Load target
    target = await comment.target  # Returns Article or Video

SQLAlchemy Comparison:
    SQLAlchemy requires:
        __mapper_args__ = {
            'polymorphic_on': type,
            'polymorphic_identity': 'article'
        }
    
    PyNext just needs:
        @polymorphic("type")
        @polymorphic.subtype("article")
"""

# Registry
from pynext.db.polymorphic.registry import (
    InheritanceStrategy,
    PolymorphicConfig,
    PolymorphicRegistry,
    get_polymorphic_registry,
    reset_polymorphic_registry,
)

# Decorators
from pynext.db.polymorphic.base import (
    polymorphic,
    PolymorphicDecorator,
    is_polymorphic,
    is_polymorphic_base,
    is_polymorphic_subtype,
    get_polymorphic_identity,
    get_polymorphic_base,
    get_discriminator_column,
    get_inheritance_strategy,
)

# Strategies
from pynext.db.polymorphic.strategies import (
    PolymorphicStrategy,
    SingleTableStrategy,
    JoinedTableStrategy,
    ConcreteTableStrategy,
    get_strategy,
)

# Generic Foreign Keys
from pynext.db.polymorphic.generic_fk import (
    GenericForeignKey,
    GenericFKConfig,
    GenericFKLoader,
    generic_fk,
    get_generic_fk_config,
    get_all_generic_fk_configs,
)

# Query Extensions
from pynext.db.polymorphic.query import (
    PolymorphicQueryMixin,
    PolymorphicQueryBuilder,
    polymorphic_query,
    instantiate_polymorphic,
)


__all__ = [
    # Registry
    "InheritanceStrategy",
    "PolymorphicConfig",
    "PolymorphicRegistry",
    "get_polymorphic_registry",
    "reset_polymorphic_registry",
    # Decorators
    "polymorphic",
    "PolymorphicDecorator",
    "is_polymorphic",
    "is_polymorphic_base",
    "is_polymorphic_subtype",
    "get_polymorphic_identity",
    "get_polymorphic_base",
    "get_discriminator_column",
    "get_inheritance_strategy",
    # Strategies
    "PolymorphicStrategy",
    "SingleTableStrategy",
    "JoinedTableStrategy",
    "ConcreteTableStrategy",
    "get_strategy",
    # Generic Foreign Keys
    "GenericForeignKey",
    "GenericFKConfig",
    "GenericFKLoader",
    "generic_fk",
    "get_generic_fk_config",
    "get_all_generic_fk_configs",
    # Query Extensions
    "PolymorphicQueryMixin",
    "PolymorphicQueryBuilder",
    "polymorphic_query",
    "instantiate_polymorphic",
]

