"""
Tests for PyNext Static Site Generation (SSG).
"""

import pytest
import asyncio
from pathlib import Path
from pynext.core.static import (
    static_page,
    static_props,
    static_paths,
    StaticPageConfig,
    StaticPath,
    GenerationMode,
    StaticPageMeta,
    StaticAnalyzer,
    get_static_pages,
    get_static_props_func,
    get_static_paths_func,
    get_build_paths,
    get_page_props,
    compute_page_hash,
    analyze_page,
)


class TestStaticPageConfig:
    """Tests for StaticPageConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = StaticPageConfig()
        
        assert config.mode == GenerationMode.STATIC
        assert config.revalidate is None
        assert config.fallback is False
        assert config.hydrate_islands_only is True
        assert config.ship_zero_js is True
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = StaticPageConfig(
            mode=GenerationMode.ISR,
            revalidate=60,
            fallback=True,
        )
        
        assert config.mode == GenerationMode.ISR
        assert config.revalidate == 60
        assert config.fallback is True


class TestStaticPath:
    """Tests for StaticPath."""
    
    def test_simple_path(self):
        """Test simple path generation."""
        path = StaticPath(params={})
        result = path.get_path("/about")
        
        assert result == "/about"
    
    def test_dynamic_path(self):
        """Test dynamic path generation."""
        path = StaticPath(params={"slug": "hello-world"})
        result = path.get_path("/blog/[slug]")
        
        assert result == "/blog/hello-world"
    
    def test_catch_all_path(self):
        """Test catch-all path generation."""
        path = StaticPath(params={"path": "docs/getting-started"})
        result = path.get_path("/[...path]")
        
        assert result == "/docs/getting-started"
    
    def test_multiple_params(self):
        """Test multiple parameters."""
        path = StaticPath(params={"category": "tech", "slug": "python-tips"})
        result = path.get_path("/blog/[category]/[slug]")
        
        assert result == "/blog/tech/python-tips"


class TestStaticPageDecorator:
    """Tests for @static_page decorator."""
    
    def test_basic_decorator(self):
        """Test basic decorator application."""
        @static_page()
        def about_page():
            return "<h1>About</h1>"
        
        assert hasattr(about_page, '_is_static_page')
        assert about_page._is_static_page is True
        assert about_page._static_config.mode == GenerationMode.STATIC
    
    def test_decorator_with_config(self):
        """Test decorator with custom config."""
        config = StaticPageConfig(
            mode=GenerationMode.ISR,
            revalidate=120,
        )
        
        @static_page(config=config)
        def blog_page():
            return "<h1>Blog</h1>"
        
        assert blog_page._static_config.mode == GenerationMode.ISR
        assert blog_page._static_config.revalidate == 120
    
    def test_decorator_kwargs(self):
        """Test decorator with keyword arguments."""
        @static_page(revalidate=60, fallback=True)
        def products_page():
            return "<h1>Products</h1>"
        
        # Config should be created from kwargs
        assert hasattr(products_page, '_static_config')
    
    def test_decorated_function_still_works(self):
        """Test that decorated function is still callable."""
        @static_page()
        def test_page():
            return "<div>Test Content</div>"
        
        result = test_page()
        assert result == "<div>Test Content</div>"


class TestStaticPropsDecorator:
    """Tests for @static_props decorator."""
    
    def test_basic_static_props(self):
        """Test basic static props decorator."""
        @static_props
        def get_props(params):
            return {"title": "Test"}
        
        assert hasattr(get_props, '_is_static_props')
        assert get_props._is_static_props is True
    
    def test_static_props_with_revalidate(self):
        """Test static props with revalidate."""
        @static_props(revalidate=30)
        def get_props(params):
            return {"data": "test"}
        
        assert get_props._revalidate == 30
    
    def test_async_static_props(self):
        """Test async static props function."""
        @static_props
        async def get_async_props(params):
            await asyncio.sleep(0)
            return {"async": True}
        
        assert get_async_props._is_static_props is True


class TestStaticPathsDecorator:
    """Tests for @static_paths decorator."""
    
    def test_basic_static_paths(self):
        """Test basic static paths decorator."""
        @static_paths
        def get_paths():
            return [
                {"params": {"slug": "post-1"}},
                {"params": {"slug": "post-2"}},
            ]
        
        assert hasattr(get_paths, '_is_static_paths')
        assert get_paths._is_static_paths is True
    
    def test_static_paths_with_fallback(self):
        """Test static paths with fallback."""
        @static_paths(fallback=True)
        def get_paths():
            return [{"params": {"id": "1"}}]
        
        assert get_paths._fallback is True
    
    def test_async_static_paths(self):
        """Test async static paths function."""
        @static_paths
        async def get_async_paths():
            await asyncio.sleep(0)
            return [{"params": {"id": "async-1"}}]
        
        assert get_async_paths._is_static_paths is True


class TestStaticAnalyzer:
    """Tests for StaticAnalyzer."""
    
    def test_static_content_detection(self):
        """Test detection of fully static content."""
        analyzer = StaticAnalyzer()
        
        # Simple string is static
        content = "<div><h1>Hello</h1></div>"
        assert analyzer.is_fully_static(content) is True
    
    def test_get_required_js_static(self):
        """Test that static content requires no JS."""
        analyzer = StaticAnalyzer()
        
        content = "<div>Static content</div>"
        js = analyzer.get_required_js(content)
        
        assert js is None  # No JS needed
    
    def test_cache_clearing(self):
        """Test cache clearing."""
        analyzer = StaticAnalyzer()
        
        content = "test"
        analyzer.is_fully_static(content)
        
        # Cache should have entry
        assert len(analyzer._cache) > 0
        
        analyzer.clear_cache()
        assert len(analyzer._cache) == 0


class TestPageAnalysis:
    """Tests for page analysis function."""
    
    def test_analyze_static_page(self):
        """Test analyzing a static page."""
        content = "<div><h1>Static</h1><p>Content</p></div>"
        analysis = analyze_page(content)
        
        assert analysis["is_fully_static"] is True
        assert analysis["needs_js"] is False
        assert analysis["island_count"] == 0
        assert analysis["recommended_mode"] == GenerationMode.STATIC


class TestBuildHelpers:
    """Tests for build helper functions."""
    
    @pytest.mark.asyncio
    async def test_get_build_paths_no_func(self):
        """Test getting build paths without paths function."""
        paths = await get_build_paths("/about")
        
        # Should return single empty path
        assert len(paths) == 1
        assert paths[0].params == {}
    
    @pytest.mark.asyncio
    async def test_get_page_props_no_func(self):
        """Test getting page props without props function."""
        props = await get_page_props("/about", {})
        
        # Should return params only
        assert "params" in props
    
    def test_compute_page_hash(self):
        """Test page hash computation."""
        html = "<div>Test</div>"
        props = {"title": "Test"}
        
        hash1 = compute_page_hash(html, props)
        hash2 = compute_page_hash(html, props)
        
        # Same input should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 12
    
    def test_compute_page_hash_different_input(self):
        """Test hash changes with different input."""
        html1 = "<div>Test 1</div>"
        html2 = "<div>Test 2</div>"
        props = {}
        
        hash1 = compute_page_hash(html1, props)
        hash2 = compute_page_hash(html2, props)
        
        assert hash1 != hash2


class TestGenerationMode:
    """Tests for GenerationMode enum."""
    
    def test_all_modes_exist(self):
        """Test all generation modes are defined."""
        assert GenerationMode.STATIC.value == "static"
        assert GenerationMode.SSR.value == "ssr"
        assert GenerationMode.ISR.value == "isr"
        assert GenerationMode.HYBRID.value == "hybrid"


class TestIntegration:
    """Integration tests for SSG workflow."""
    
    def test_full_ssg_workflow(self):
        """Test complete SSG workflow."""
        # Define a static page with props and paths
        @static_page()
        def blog_post(title: str, content: str):
            return f"<article><h1>{title}</h1><p>{content}</p></article>"
        
        @static_props
        def get_blog_props(params):
            return {
                "title": f"Post {params.get('slug', 'unknown')}",
                "content": "This is the content.",
            }
        
        @static_paths
        def get_blog_paths():
            return [
                {"params": {"slug": "first-post"}},
                {"params": {"slug": "second-post"}},
            ]
        
        # Verify decorators applied correctly
        assert blog_post._is_static_page
        assert get_blog_props._is_static_props
        assert get_blog_paths._is_static_paths
        
        # Render a page
        result = blog_post(title="Test", content="Hello")
        assert "<h1>Test</h1>" in result
        assert "<p>Hello</p>" in result

