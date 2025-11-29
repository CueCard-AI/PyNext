"""
PyNext SEO Module.

Provides sitemap generation and robots.txt configuration.

Example:
    from pynext import sitemap, RobotsConfig
    
    @sitemap(priority=0.8)
    @page
    def ProductPage(id: str):
        return Product(id)
"""

from pynext.seo.sitemap import (
    SitemapEntry,
    SitemapConfig,
    sitemap,
    get_sitemap_config,
    has_sitemap_config,
    SitemapGenerator,
    clear_sitemap_configs,
)

from pynext.seo.robots import (
    RobotsRule,
    RobotsConfig,
    robots_allow_all,
    robots_disallow_all,
    RobotsGenerator,
)

__all__ = [
    # Sitemap
    "SitemapEntry",
    "SitemapConfig",
    "sitemap",
    "get_sitemap_config",
    "has_sitemap_config",
    "SitemapGenerator",
    "clear_sitemap_configs",
    # Robots
    "RobotsRule",
    "RobotsConfig",
    "robots_allow_all",
    "robots_disallow_all",
    "RobotsGenerator",
]

