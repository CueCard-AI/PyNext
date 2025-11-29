"""
Unit tests for SEO (Sitemap & Robots.txt) features.

Tests cover:
- SitemapEntry dataclass
- SitemapConfig and @sitemap decorator
- SitemapGenerator auto-discovery and XML generation
- Sitemap index splitting
- RobotsRule and RobotsConfig
- Convenience functions (robots_allow_all, robots_disallow_all)
- CLI integration
"""

import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import os


# ============================================
# SitemapEntry Tests (10 tests)
# ============================================

class TestSitemapEntry:
    """Tests for SitemapEntry dataclass."""
    
    def test_create_basic_entry(self):
        """Test creating a basic sitemap entry."""
        from pynext.seo.sitemap import SitemapEntry
        
        entry = SitemapEntry(loc="https://example.com/page")
        
        assert entry.loc == "https://example.com/page"
        assert entry.lastmod is None
        assert entry.changefreq is None
        assert entry.priority is None
    
    def test_create_full_entry(self):
        """Test creating entry with all fields."""
        from pynext.seo.sitemap import SitemapEntry
        
        entry = SitemapEntry(
            loc="https://example.com/products/123",
            lastmod="2024-01-15",
            changefreq="daily",
            priority=0.8,
        )
        
        assert entry.loc == "https://example.com/products/123"
        assert entry.lastmod == "2024-01-15"
        assert entry.changefreq == "daily"
        assert entry.priority == 0.8
    
    def test_entry_requires_absolute_url(self):
        """Test that relative URLs raise error."""
        from pynext.seo.sitemap import SitemapEntry
        
        with pytest.raises(ValueError) as exc_info:
            SitemapEntry(loc="/products/123")
        
        assert "absolute URL" in str(exc_info.value)
    
    def test_entry_requires_loc(self):
        """Test that empty loc raises error."""
        from pynext.seo.sitemap import SitemapEntry
        
        with pytest.raises(ValueError) as exc_info:
            SitemapEntry(loc="")
        
        assert "required" in str(exc_info.value)
    
    def test_priority_validation(self):
        """Test priority must be 0.0-1.0."""
        from pynext.seo.sitemap import SitemapEntry
        
        with pytest.raises(ValueError) as exc_info:
            SitemapEntry(loc="https://example.com", priority=1.5)
        
        assert "0.0-1.0" in str(exc_info.value)
    
    def test_priority_negative_invalid(self):
        """Test negative priority is invalid."""
        from pynext.seo.sitemap import SitemapEntry
        
        with pytest.raises(ValueError):
            SitemapEntry(loc="https://example.com", priority=-0.5)
    
    def test_changefreq_validation(self):
        """Test changefreq must be valid value."""
        from pynext.seo.sitemap import SitemapEntry
        
        with pytest.raises(ValueError) as exc_info:
            SitemapEntry(loc="https://example.com", changefreq="invalid")
        
        assert "changefreq" in str(exc_info.value)
    
    def test_to_xml_basic(self):
        """Test XML generation for basic entry."""
        from pynext.seo.sitemap import SitemapEntry
        
        entry = SitemapEntry(loc="https://example.com/page")
        xml = entry.to_xml()
        
        assert "<url>" in xml
        assert "<loc>https://example.com/page</loc>" in xml
        assert "</url>" in xml
    
    def test_to_xml_full(self):
        """Test XML generation for full entry."""
        from pynext.seo.sitemap import SitemapEntry
        
        entry = SitemapEntry(
            loc="https://example.com/page",
            lastmod="2024-01-15",
            changefreq="daily",
            priority=0.8,
        )
        xml = entry.to_xml()
        
        assert "<lastmod>2024-01-15</lastmod>" in xml
        assert "<changefreq>daily</changefreq>" in xml
        assert "<priority>0.8</priority>" in xml
    
    def test_to_xml_escapes_special_chars(self):
        """Test XML escapes special characters."""
        from pynext.seo.sitemap import SitemapEntry
        
        entry = SitemapEntry(loc="https://example.com/page?foo=1&bar=2")
        xml = entry.to_xml()
        
        assert "&amp;" in xml


# ============================================
# SitemapConfig Tests (8 tests)
# ============================================

class TestSitemapConfig:
    """Tests for SitemapConfig dataclass."""
    
    def test_default_values(self):
        """Test default config values."""
        from pynext.seo.sitemap import SitemapConfig
        
        config = SitemapConfig()
        
        assert config.priority == 0.5
        assert config.changefreq == "weekly"
        assert config.lastmod == "auto"
        assert config.include is True
    
    def test_custom_values(self):
        """Test custom config values."""
        from pynext.seo.sitemap import SitemapConfig
        
        config = SitemapConfig(
            priority=0.9,
            changefreq="daily",
            lastmod="2024-01-15",
            include=False,
        )
        
        assert config.priority == 0.9
        assert config.changefreq == "daily"
        assert config.lastmod == "2024-01-15"
        assert config.include is False
    
    def test_priority_validation(self):
        """Test priority must be 0.0-1.0."""
        from pynext.seo.sitemap import SitemapConfig
        
        with pytest.raises(ValueError):
            SitemapConfig(priority=1.5)
    
    def test_changefreq_validation(self):
        """Test changefreq must be valid."""
        from pynext.seo.sitemap import SitemapConfig
        
        with pytest.raises(ValueError):
            SitemapConfig(changefreq="invalid")
    
    def test_to_dict(self):
        """Test serialization to dict."""
        from pynext.seo.sitemap import SitemapConfig
        
        config = SitemapConfig(priority=0.8, changefreq="daily")
        data = config.to_dict()
        
        assert data["priority"] == 0.8
        assert data["changefreq"] == "daily"
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        from pynext.seo.sitemap import SitemapConfig
        
        data = {"priority": 0.7, "changefreq": "monthly"}
        config = SitemapConfig.from_dict(data)
        
        assert config.priority == 0.7
        assert config.changefreq == "monthly"
    
    def test_from_dict_defaults(self):
        """Test from_dict uses defaults for missing values."""
        from pynext.seo.sitemap import SitemapConfig
        
        data = {}
        config = SitemapConfig.from_dict(data)
        
        assert config.priority == 0.5
        assert config.include is True
    
    def test_all_changefreq_values(self):
        """Test all valid changefreq values work."""
        from pynext.seo.sitemap import SitemapConfig
        
        valid_freqs = ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"]
        
        for freq in valid_freqs:
            config = SitemapConfig(changefreq=freq)
            assert config.changefreq == freq


# ============================================
# @sitemap Decorator Tests (12 tests)
# ============================================

class TestSitemapDecorator:
    """Tests for @sitemap decorator."""
    
    def setup_method(self):
        """Clear registry before each test."""
        from pynext.seo.sitemap import clear_sitemap_configs
        clear_sitemap_configs()
    
    def test_basic_decorator(self):
        """Test basic decorator application."""
        from pynext.seo.sitemap import sitemap, get_sitemap_config
        
        @sitemap()
        def my_page():
            return "Hello"
        
        config = get_sitemap_config(my_page)
        
        assert config is not None
        assert config.priority == 0.5
    
    def test_decorator_with_params(self):
        """Test decorator with parameters."""
        from pynext.seo.sitemap import sitemap, get_sitemap_config
        
        @sitemap(priority=0.9, changefreq="daily")
        def my_page():
            return "Hello"
        
        config = get_sitemap_config(my_page)
        
        assert config.priority == 0.9
        assert config.changefreq == "daily"
    
    def test_decorator_include_false(self):
        """Test decorator with include=False."""
        from pynext.seo.sitemap import sitemap, get_sitemap_config
        
        @sitemap(include=False)
        def admin_page():
            return "Admin"
        
        config = get_sitemap_config(admin_page)
        
        assert config.include is False
    
    def test_has_sitemap_config(self):
        """Test has_sitemap_config helper."""
        from pynext.seo.sitemap import sitemap, has_sitemap_config
        
        @sitemap()
        def with_config():
            pass
        
        def without_config():
            pass
        
        assert has_sitemap_config(with_config) is True
        assert has_sitemap_config(without_config) is False
    
    def test_get_sitemap_config_none(self):
        """Test get_sitemap_config returns None for undecorated."""
        from pynext.seo.sitemap import get_sitemap_config
        
        def my_page():
            pass
        
        assert get_sitemap_config(my_page) is None
    
    def test_decorator_preserves_function(self):
        """Test decorator preserves function attributes."""
        from pynext.seo.sitemap import sitemap
        
        @sitemap()
        def my_page():
            """My docstring."""
            return "Hello"
        
        assert my_page.__name__ == "my_page"
        assert my_page.__doc__ == "My docstring."
    
    def test_decorator_function_still_callable(self):
        """Test decorated function is still callable."""
        from pynext.seo.sitemap import sitemap
        
        @sitemap()
        def my_page():
            return "Hello"
        
        result = my_page()
        assert result == "Hello"
    
    def test_decorator_stacking(self):
        """Test decorator works with other decorators."""
        from pynext.seo.sitemap import sitemap, get_sitemap_config
        
        def other_decorator(fn):
            fn.other_attr = True
            return fn
        
        @other_decorator
        @sitemap(priority=0.8)
        def my_page():
            return "Hello"
        
        config = get_sitemap_config(my_page)
        assert config is not None
        assert hasattr(my_page, "other_attr")
    
    def test_multiple_pages_independent(self):
        """Test multiple pages have independent configs."""
        from pynext.seo.sitemap import sitemap, get_sitemap_config
        
        @sitemap(priority=0.9)
        def page_a():
            pass
        
        @sitemap(priority=0.3)
        def page_b():
            pass
        
        assert get_sitemap_config(page_a).priority == 0.9
        assert get_sitemap_config(page_b).priority == 0.3
    
    def test_with_page_decorator(self):
        """Test sitemap with @page decorator."""
        from pynext.seo.sitemap import sitemap, get_sitemap_config
        from pynext.core.component import page
        
        @sitemap(priority=0.8)
        @page
        def MyPage():
            return "Hello"
        
        config = get_sitemap_config(MyPage)
        assert config is not None
    
    def test_lastmod_auto(self):
        """Test lastmod='auto' default."""
        from pynext.seo.sitemap import sitemap, get_sitemap_config
        
        @sitemap()
        def my_page():
            pass
        
        config = get_sitemap_config(my_page)
        assert config.lastmod == "auto"
    
    def test_lastmod_specific_date(self):
        """Test lastmod with specific date."""
        from pynext.seo.sitemap import sitemap, get_sitemap_config
        
        @sitemap(lastmod="2024-01-15")
        def my_page():
            pass
        
        config = get_sitemap_config(my_page)
        assert config.lastmod == "2024-01-15"


# ============================================
# SitemapGenerator Tests (14 tests)
# ============================================

class TestSitemapGenerator:
    """Tests for SitemapGenerator."""
    
    def test_create_generator(self):
        """Test creating a generator."""
        from pynext.seo.sitemap import SitemapGenerator
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        
        assert generator.base_url == "https://example.com"
    
    def test_base_url_trailing_slash_removed(self):
        """Test trailing slash is removed from base URL."""
        from pynext.seo.sitemap import SitemapGenerator
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com/")
        
        assert generator.base_url == "https://example.com"
    
    def test_generate_xml_empty(self):
        """Test generating XML with no entries."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        xml = generator.generate_xml([])
        
        assert '<?xml version="1.0"' in xml
        assert '<urlset' in xml
        assert '</urlset>' in xml
    
    def test_generate_xml_with_entries(self):
        """Test generating XML with entries."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        
        entries = [
            SitemapEntry(loc="https://example.com/page1"),
            SitemapEntry(loc="https://example.com/page2", priority=0.8),
        ]
        
        xml = generator.generate_xml(entries)
        
        assert "https://example.com/page1" in xml
        assert "https://example.com/page2" in xml
        assert "<priority>0.8</priority>" in xml
    
    def test_url_count_property(self):
        """Test url_count property."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        generator._entries = [
            SitemapEntry(loc="https://example.com/1"),
            SitemapEntry(loc="https://example.com/2"),
        ]
        
        assert generator.url_count == 2
    
    def test_needs_index_under_limit(self):
        """Test needs_index returns False under limit."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        entries = [SitemapEntry(loc="https://example.com/1")]
        
        assert generator.needs_index(entries) is False
    
    def test_needs_index_over_limit(self):
        """Test needs_index returns True over limit."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        
        # Create 50,001 entries (just over limit)
        entries = [SitemapEntry(loc=f"https://example.com/{i}") for i in range(50001)]
        
        assert generator.needs_index(entries) is True
    
    def test_generate_index(self):
        """Test generating sitemap index."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        
        # Create enough entries to split
        entries = [SitemapEntry(loc=f"https://example.com/{i}") for i in range(100)]
        
        # Temporarily lower the limit for testing
        original_limit = SitemapGenerator.MAX_URLS_PER_SITEMAP
        SitemapGenerator.MAX_URLS_PER_SITEMAP = 30
        
        try:
            index_xml, sitemaps = generator.generate_index(entries)
            
            # Should have multiple sitemaps
            assert len(sitemaps) > 1
            assert "sitemap-1.xml" in sitemaps[0][0]
            
            # Index should reference sitemaps
            assert "<sitemapindex" in index_xml
            assert "sitemap-1.xml" in index_xml
        finally:
            SitemapGenerator.MAX_URLS_PER_SITEMAP = original_limit
    
    def test_generate_index_single_sitemap(self):
        """Test generate_index with single sitemap (under limit)."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        entries = [SitemapEntry(loc="https://example.com/1")]
        
        index_xml, sitemaps = generator.generate_index(entries)
        
        # No index needed
        assert index_xml == ""
        # Single sitemap
        assert len(sitemaps) == 1
        assert sitemaps[0][0] == "sitemap.xml"
    
    def test_write_to_directory(self):
        """Test writing sitemaps to directory."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SitemapGenerator(MockRouter(), "https://example.com")
            generator._entries = [
                SitemapEntry(loc="https://example.com/1"),
                SitemapEntry(loc="https://example.com/2"),
            ]
            
            written = generator.write_to_directory(Path(tmpdir))
            
            assert len(written) == 1
            assert written[0].name == "sitemap.xml"
            assert written[0].exists()
            
            content = written[0].read_text()
            assert "https://example.com/1" in content
    
    def test_write_to_directory_with_index(self):
        """Test writing sitemap index to directory."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SitemapGenerator(MockRouter(), "https://example.com")
            
            # Lower limit for testing
            original_limit = SitemapGenerator.MAX_URLS_PER_SITEMAP
            SitemapGenerator.MAX_URLS_PER_SITEMAP = 10
            
            try:
                entries = [SitemapEntry(loc=f"https://example.com/{i}") for i in range(25)]
                written = generator.write_to_directory(Path(tmpdir), entries)
                
                # Should have index + 3 sitemaps
                assert len(written) >= 3
                
                # Check files exist
                for path in written:
                    assert path.exists()
            finally:
                SitemapGenerator.MAX_URLS_PER_SITEMAP = original_limit
    
    def test_max_urls_constant(self):
        """Test MAX_URLS_PER_SITEMAP constant."""
        from pynext.seo.sitemap import SitemapGenerator
        
        assert SitemapGenerator.MAX_URLS_PER_SITEMAP == 50000
    
    def test_discover_urls_empty(self):
        """Test discover_urls with no routes."""
        from pynext.seo.sitemap import SitemapGenerator
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        entries = generator.discover_urls()
        
        assert entries == []
    
    def test_generate_method(self):
        """Test generate() method discovers and generates."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        generator._entries = [SitemapEntry(loc="https://example.com/test")]
        
        xml = generator.generate()
        
        assert "https://example.com/test" in xml


# ============================================
# RobotsRule Tests (8 tests)
# ============================================

class TestRobotsRule:
    """Tests for RobotsRule dataclass."""
    
    def test_default_values(self):
        """Test default rule values."""
        from pynext.seo.robots import RobotsRule
        
        rule = RobotsRule()
        
        assert rule.user_agent == "*"
        assert rule.allow == []
        assert rule.disallow == []
        assert rule.crawl_delay is None
    
    def test_custom_values(self):
        """Test custom rule values."""
        from pynext.seo.robots import RobotsRule
        
        rule = RobotsRule(
            user_agent="Googlebot",
            allow=["/"],
            disallow=["/admin"],
            crawl_delay=1,
        )
        
        assert rule.user_agent == "Googlebot"
        assert rule.allow == ["/"]
        assert rule.disallow == ["/admin"]
        assert rule.crawl_delay == 1
    
    def test_user_agent_required(self):
        """Test user_agent is required."""
        from pynext.seo.robots import RobotsRule
        
        with pytest.raises(ValueError):
            RobotsRule(user_agent="")
    
    def test_crawl_delay_validation(self):
        """Test crawl_delay must be non-negative."""
        from pynext.seo.robots import RobotsRule
        
        with pytest.raises(ValueError):
            RobotsRule(crawl_delay=-1)
    
    def test_to_text_basic(self):
        """Test basic text generation."""
        from pynext.seo.robots import RobotsRule
        
        rule = RobotsRule()
        text = rule.to_text()
        
        assert "User-agent: *" in text
    
    def test_to_text_with_paths(self):
        """Test text generation with paths."""
        from pynext.seo.robots import RobotsRule
        
        rule = RobotsRule(
            allow=["/public"],
            disallow=["/admin", "/api"],
        )
        text = rule.to_text()
        
        assert "Allow: /public" in text
        assert "Disallow: /admin" in text
        assert "Disallow: /api" in text
    
    def test_to_text_with_crawl_delay(self):
        """Test text generation with crawl-delay."""
        from pynext.seo.robots import RobotsRule
        
        rule = RobotsRule(user_agent="Googlebot", crawl_delay=2)
        text = rule.to_text()
        
        assert "User-agent: Googlebot" in text
        assert "Crawl-delay: 2" in text
    
    def test_multiple_allow_paths(self):
        """Test multiple allow paths."""
        from pynext.seo.robots import RobotsRule
        
        rule = RobotsRule(allow=["/a", "/b", "/c"])
        text = rule.to_text()
        
        assert text.count("Allow:") == 3


# ============================================
# RobotsConfig Tests (10 tests)
# ============================================

class TestRobotsConfig:
    """Tests for RobotsConfig dataclass."""
    
    def test_default_config(self):
        """Test default config creates allow-all rule."""
        from pynext.seo.robots import RobotsConfig
        
        config = RobotsConfig()
        
        # Should have default allow-all rule
        assert len(config.rules) == 1
        assert config.rules[0].user_agent == "*"
        assert "/" in config.rules[0].allow
    
    def test_custom_rules(self):
        """Test config with custom rules."""
        from pynext.seo.robots import RobotsConfig, RobotsRule
        
        config = RobotsConfig(
            rules=[
                RobotsRule(user_agent="*", disallow=["/admin"]),
            ],
        )
        
        assert len(config.rules) == 1
        assert config.rules[0].disallow == ["/admin"]
    
    def test_sitemap_default(self):
        """Test sitemap is included by default."""
        from pynext.seo.robots import RobotsConfig
        
        config = RobotsConfig()
        
        assert config.sitemap is True
    
    def test_generate_basic(self):
        """Test generating robots.txt content."""
        from pynext.seo.robots import RobotsConfig, RobotsRule
        
        config = RobotsConfig(
            rules=[RobotsRule(user_agent="*", allow=["/"]) ],
        )
        content = config.generate("https://example.com")
        
        assert "User-agent: *" in content
        assert "Allow: /" in content
    
    def test_generate_with_sitemap(self):
        """Test sitemap URL is included."""
        from pynext.seo.robots import RobotsConfig
        
        config = RobotsConfig(sitemap=True)
        content = config.generate("https://example.com")
        
        assert "Sitemap: https://example.com/sitemap.xml" in content
    
    def test_generate_without_sitemap(self):
        """Test sitemap can be excluded."""
        from pynext.seo.robots import RobotsConfig
        
        config = RobotsConfig(sitemap=False)
        content = config.generate("https://example.com")
        
        assert "Sitemap:" not in content
    
    def test_generate_custom_sitemap_url(self):
        """Test custom sitemap URL."""
        from pynext.seo.robots import RobotsConfig
        
        config = RobotsConfig(
            sitemap=True,
            sitemap_url="https://cdn.example.com/sitemap.xml",
        )
        content = config.generate("https://example.com")
        
        assert "Sitemap: https://cdn.example.com/sitemap.xml" in content
    
    def test_generate_with_host(self):
        """Test host directive is included."""
        from pynext.seo.robots import RobotsConfig
        
        config = RobotsConfig(host="www.example.com")
        content = config.generate("https://example.com")
        
        assert "Host: www.example.com" in content
    
    def test_to_dict(self):
        """Test serialization to dict."""
        from pynext.seo.robots import RobotsConfig, RobotsRule
        
        config = RobotsConfig(
            rules=[RobotsRule(user_agent="*", allow=["/"]) ],
            sitemap=True,
        )
        data = config.to_dict()
        
        assert "rules" in data
        assert data["sitemap"] is True
    
    def test_from_dict(self):
        """Test deserialization from dict."""
        from pynext.seo.robots import RobotsConfig
        
        data = {
            "rules": [
                {"user_agent": "*", "allow": ["/"], "disallow": ["/admin"]},
            ],
            "sitemap": True,
        }
        config = RobotsConfig.from_dict(data)
        
        assert len(config.rules) == 1
        assert config.rules[0].disallow == ["/admin"]


# ============================================
# Convenience Functions Tests (6 tests)
# ============================================

class TestRobotsConvenienceFunctions:
    """Tests for robots convenience functions."""
    
    def test_robots_allow_all(self):
        """Test robots_allow_all creates correct config."""
        from pynext.seo.robots import robots_allow_all
        
        config = robots_allow_all()
        
        assert len(config.rules) == 1
        assert "/" in config.rules[0].allow
        assert config.sitemap is True
    
    def test_robots_allow_all_with_exceptions(self):
        """Test robots_allow_all with except_paths."""
        from pynext.seo.robots import robots_allow_all
        
        config = robots_allow_all(except_paths=["/admin", "/api"])
        
        assert "/admin" in config.rules[0].disallow
        assert "/api" in config.rules[0].disallow
    
    def test_robots_allow_all_no_sitemap(self):
        """Test robots_allow_all without sitemap."""
        from pynext.seo.robots import robots_allow_all
        
        config = robots_allow_all(sitemap=False)
        
        assert config.sitemap is False
    
    def test_robots_disallow_all(self):
        """Test robots_disallow_all creates correct config."""
        from pynext.seo.robots import robots_disallow_all
        
        config = robots_disallow_all()
        
        assert len(config.rules) == 1
        assert "/" in config.rules[0].disallow
        assert config.sitemap is False
    
    def test_robots_disallow_all_with_sitemap(self):
        """Test robots_disallow_all with sitemap."""
        from pynext.seo.robots import robots_disallow_all
        
        config = robots_disallow_all(sitemap=True)
        
        assert config.sitemap is True
    
    def test_robots_from_paths(self):
        """Test robots_from_paths convenience function."""
        from pynext.seo.robots import robots_from_paths
        
        config = robots_from_paths(
            allow=["/", "/products"],
            disallow=["/admin"],
        )
        
        assert "/" in config.rules[0].allow
        assert "/products" in config.rules[0].allow
        assert "/admin" in config.rules[0].disallow


# ============================================
# RobotsGenerator Tests (6 tests)
# ============================================

class TestRobotsGenerator:
    """Tests for RobotsGenerator."""
    
    def test_create_generator(self):
        """Test creating a generator."""
        from pynext.seo.robots import RobotsGenerator, RobotsConfig
        
        config = RobotsConfig()
        generator = RobotsGenerator(config, "https://example.com")
        
        assert generator.base_url == "https://example.com"
    
    def test_generate(self):
        """Test generate method."""
        from pynext.seo.robots import RobotsGenerator, RobotsConfig
        
        config = RobotsConfig()
        generator = RobotsGenerator(config, "https://example.com")
        
        content = generator.generate()
        
        assert "User-agent:" in content
    
    def test_write_to_file(self):
        """Test writing to file."""
        from pynext.seo.robots import RobotsGenerator, RobotsConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RobotsConfig()
            generator = RobotsGenerator(config, "https://example.com")
            
            output_path = Path(tmpdir) / "robots.txt"
            written = generator.write_to_file(output_path)
            
            assert written.exists()
            assert "User-agent:" in written.read_text()
    
    def test_validate_no_warnings(self):
        """Test validate with no issues."""
        from pynext.seo.robots import RobotsGenerator, RobotsConfig, RobotsRule
        
        config = RobotsConfig(
            rules=[RobotsRule(allow=["/"]) ],
        )
        generator = RobotsGenerator(config, "https://example.com")
        
        warnings = generator.validate()
        
        assert len(warnings) == 0
    
    def test_validate_conflicting_paths(self):
        """Test validate catches conflicting paths."""
        from pynext.seo.robots import RobotsGenerator, RobotsConfig, RobotsRule
        
        config = RobotsConfig(
            rules=[
                RobotsRule(allow=["/path"], disallow=["/path"]),
            ],
        )
        generator = RobotsGenerator(config, "https://example.com")
        
        warnings = generator.validate()
        
        assert len(warnings) > 0
        assert "both allowed and disallowed" in warnings[0]
    
    def test_validate_relative_sitemap_url(self):
        """Test validate warns on relative sitemap URL."""
        from pynext.seo.robots import RobotsGenerator, RobotsConfig
        
        config = RobotsConfig(
            sitemap_url="/sitemap.xml",
        )
        generator = RobotsGenerator(config, "https://example.com")
        
        warnings = generator.validate()
        
        assert len(warnings) > 0
        assert "absolute" in warnings[0]


# ============================================
# Integration Tests (8 tests)
# ============================================

class TestSEOIntegration:
    """Integration tests for SEO features."""
    
    def test_exports_from_pynext(self):
        """Test all exports are available from pynext."""
        from pynext import (
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
        
        # All imports should work
        assert SitemapEntry is not None
        assert sitemap is not None
        assert RobotsConfig is not None
    
    def test_exports_from_seo_module(self):
        """Test all exports from seo submodule."""
        from pynext.seo import (
            SitemapEntry,
            SitemapConfig,
            sitemap,
            SitemapGenerator,
            RobotsRule,
            RobotsConfig,
            robots_allow_all,
            robots_disallow_all,
        )
        
        assert SitemapEntry is not None
    
    def test_sitemap_with_page_decorator(self):
        """Test sitemap works with page decorator."""
        from pynext import page, sitemap, get_sitemap_config
        from pynext.seo.sitemap import clear_sitemap_configs
        
        clear_sitemap_configs()
        
        @sitemap(priority=0.8)
        @page
        def ProductPage(id: str):
            return f"Product {id}"
        
        config = get_sitemap_config(ProductPage)
        assert config is not None
        assert config.priority == 0.8
    
    def test_full_sitemap_generation_flow(self):
        """Test complete sitemap generation flow."""
        from pynext.seo.sitemap import SitemapGenerator, SitemapEntry
        
        class MockRouter:
            routes = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = SitemapGenerator(MockRouter(), "https://example.com")
            generator._entries = [
                SitemapEntry(loc="https://example.com/"),
                SitemapEntry(loc="https://example.com/about", priority=0.7),
                SitemapEntry(loc="https://example.com/products", changefreq="daily"),
            ]
            
            written = generator.write_to_directory(Path(tmpdir))
            
            assert len(written) == 1
            content = written[0].read_text()
            
            assert "https://example.com/" in content
            assert "https://example.com/about" in content
            assert "<priority>0.7</priority>" in content
    
    def test_full_robots_generation_flow(self):
        """Test complete robots.txt generation flow."""
        from pynext.seo.robots import RobotsConfig, RobotsRule, RobotsGenerator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = RobotsConfig(
                rules=[
                    RobotsRule(user_agent="*", allow=["/"], disallow=["/admin"]),
                    RobotsRule(user_agent="Googlebot", crawl_delay=1),
                ],
                sitemap=True,
            )
            
            generator = RobotsGenerator(config, "https://example.com")
            output = Path(tmpdir) / "robots.txt"
            generator.write_to_file(output)
            
            content = output.read_text()
            
            assert "User-agent: *" in content
            assert "Disallow: /admin" in content
            assert "User-agent: Googlebot" in content
            assert "Crawl-delay: 1" in content
            assert "Sitemap: https://example.com/sitemap.xml" in content
    
    def test_changefreq_enum(self):
        """Test ChangeFreq enum values."""
        from pynext.seo.sitemap import ChangeFreq
        
        assert ChangeFreq.DAILY.value == "daily"
        assert ChangeFreq.WEEKLY.value == "weekly"
        assert ChangeFreq.MONTHLY.value == "monthly"
    
    def test_add_static_urls(self):
        """Test add_static_urls function."""
        from pynext.seo.sitemap import SitemapGenerator, add_static_urls
        
        class MockRouter:
            routes = []
        
        generator = SitemapGenerator(MockRouter(), "https://example.com")
        add_static_urls(generator, [
            "https://example.com/static-page",
            "https://example.com/external",
        ])
        
        assert generator.url_count == 2
    
    def test_merge_sitemaps(self):
        """Test merge_sitemaps function."""
        from pynext.seo.sitemap import merge_sitemaps
        
        sitemap1 = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/1</loc></url>
</urlset>"""
        
        sitemap2 = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/2</loc></url>
</urlset>"""
        
        merged = merge_sitemaps([sitemap1, sitemap2])
        
        assert "https://example.com/1" in merged
        assert "https://example.com/2" in merged
        assert merged.count("<url>") == 2

