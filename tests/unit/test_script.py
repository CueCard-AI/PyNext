"""
Unit tests for Script Optimization.

Tests:
- Script component with native loading
- Script strategies
- Preload generation
- Lazy loading
- Worker scripts
"""

import pytest
from pynext.core.script import (
    Script,
    InlineScript,
    ModuleScript,
    AnalyticsScript,
    WorkerScript,
    ImportMap,
    ScriptConfig,
    ScriptRegistry,
    ScriptStrategy,
    ScriptType,
    get_script_registry,
    get_head_scripts,
    get_body_scripts,
    clear_scripts,
    _render_script_tag,
)


class TestScriptComponent:
    """Tests for the Script component."""
    
    def setup_method(self):
        """Clear scripts before each test."""
        clear_scripts()
    
    def test_script_registers_with_registry(self):
        """Script() should register with the global registry."""
        registry = get_script_registry()
        
        Script(src="/js/app.js")
        
        scripts = registry.get_by_strategy(ScriptStrategy.AFTER_INTERACTIVE)
        assert len(scripts) >= 1
    
    def test_script_returns_empty_string(self):
        """Script() should return empty string (rendered in head/body)."""
        result = Script(src="/js/app.js")
        assert result == ""
    
    def test_script_with_strategy(self):
        """Script should respect strategy."""
        Script(src="/js/critical.js", strategy="beforeInteractive")
        Script(src="/js/lazy.js", strategy="lazyOnload")
        
        registry = get_script_registry()
        
        head_scripts = registry.get_by_strategy(ScriptStrategy.BEFORE_INTERACTIVE)
        lazy_scripts = registry.get_by_strategy(ScriptStrategy.LAZY_ONLOAD)
        
        assert any(s.src == "/js/critical.js" for s in head_scripts)
        assert any(s.src == "/js/lazy.js" for s in lazy_scripts)


class TestScriptRegistry:
    """Tests for ScriptRegistry."""
    
    def test_registry_register(self):
        """Registry should register scripts and return ID."""
        registry = ScriptRegistry()
        
        config = ScriptConfig(src="/js/app.js")
        script_id = registry.register(config)
        
        assert script_id
        assert len(script_id) == 12
    
    def test_registry_get_by_strategy(self):
        """Registry should filter by strategy."""
        registry = ScriptRegistry()
        
        registry.register(ScriptConfig(
            src="/js/head.js",
            strategy=ScriptStrategy.BEFORE_INTERACTIVE,
        ))
        registry.register(ScriptConfig(
            src="/js/body.js",
            strategy=ScriptStrategy.AFTER_INTERACTIVE,
        ))
        
        head = registry.get_by_strategy(ScriptStrategy.BEFORE_INTERACTIVE)
        body = registry.get_by_strategy(ScriptStrategy.AFTER_INTERACTIVE)
        
        assert len(head) == 1
        assert len(body) == 1
    
    def test_registry_get_preload_links(self):
        """Registry should generate preload links."""
        registry = ScriptRegistry()
        
        registry.register(ScriptConfig(
            src="/js/preload.js",
            preload=True,
        ))
        
        links = registry.get_preload_links()
        assert len(links) == 1
        assert 'rel="preload"' in links[0]
    
    def test_registry_clear(self):
        """Registry should clear all scripts."""
        registry = ScriptRegistry()
        
        registry.register(ScriptConfig(src="/js/test.js"))
        registry.clear()
        
        assert len(registry.get_by_strategy(ScriptStrategy.AFTER_INTERACTIVE)) == 0


class TestScriptConfig:
    """Tests for ScriptConfig."""
    
    def test_default_config(self):
        """ScriptConfig should have sensible defaults."""
        config = ScriptConfig(src="/js/app.js")
        
        assert config.strategy == ScriptStrategy.AFTER_INTERACTIVE
        assert config.type == ScriptType.JAVASCRIPT
        assert config.defer is True
        assert config.async_ is False
    
    def test_module_config(self):
        """ScriptConfig should support modules."""
        config = ScriptConfig(
            src="/js/app.js",
            type=ScriptType.MODULE,
            strategy=ScriptStrategy.MODULE,
        )
        
        assert config.type == ScriptType.MODULE


class TestScriptRendering:
    """Tests for script tag rendering."""
    
    def test_render_basic_script(self):
        """Should render basic script tag."""
        config = ScriptConfig(src="/js/app.js")
        html = _render_script_tag(config)
        
        assert '<script' in html
        assert 'src="/js/app.js"' in html
        assert 'defer' in html
    
    def test_render_async_script(self):
        """Should render async script tag."""
        config = ScriptConfig(src="/js/app.js", async_=True, defer=False)
        html = _render_script_tag(config)
        
        assert 'async' in html
    
    def test_render_module_script(self):
        """Should render module script tag."""
        config = ScriptConfig(
            src="/js/app.js",
            type=ScriptType.MODULE,
        )
        html = _render_script_tag(config)
        
        assert 'type="module"' in html
    
    def test_render_inline_script(self):
        """Should render inline script."""
        config = ScriptConfig(inline="console.log('test');")
        html = _render_script_tag(config)
        
        assert "console.log('test');" in html
    
    def test_render_with_integrity(self):
        """Should render script with SRI."""
        config = ScriptConfig(
            src="/js/app.js",
            integrity="sha384-abc123",
        )
        html = _render_script_tag(config)
        
        assert 'integrity="sha384-abc123"' in html


class TestScriptHelpers:
    """Tests for script helper functions."""
    
    def setup_method(self):
        """Clear scripts before each test."""
        clear_scripts()
    
    def test_inline_script(self):
        """InlineScript should create inline script."""
        InlineScript("console.log('hello');")
        
        registry = get_script_registry()
        scripts = registry.get_by_strategy(ScriptStrategy.AFTER_INTERACTIVE)
        
        assert any(s.inline == "console.log('hello');" for s in scripts)
    
    def test_module_script(self):
        """ModuleScript should create module script."""
        ModuleScript("/js/module.js")
        
        registry = get_script_registry()
        scripts = registry.get_by_strategy(ScriptStrategy.MODULE)
        
        assert any(s.src == "/js/module.js" for s in scripts)
    
    def test_analytics_script(self):
        """AnalyticsScript should create lazy script."""
        AnalyticsScript("https://example.com/analytics.js")
        
        registry = get_script_registry()
        scripts = registry.get_by_strategy(ScriptStrategy.LAZY_ONLOAD)
        
        assert any(s.src == "https://example.com/analytics.js" for s in scripts)
    
    def test_worker_script(self):
        """WorkerScript should create worker script."""
        WorkerScript("/workers/heavy.js")
        
        registry = get_script_registry()
        scripts = registry.get_by_strategy(ScriptStrategy.WORKER)
        
        assert any(s.src == "/workers/heavy.js" for s in scripts)


class TestImportMap:
    """Tests for ImportMap."""
    
    def setup_method(self):
        """Clear scripts before each test."""
        clear_scripts()
    
    def test_import_map_creates_script(self):
        """ImportMap should create importmap script."""
        ImportMap({
            "lodash": "https://cdn.example.com/lodash.js",
        })
        
        registry = get_script_registry()
        scripts = registry.get_by_strategy(ScriptStrategy.BEFORE_INTERACTIVE)
        
        # Find importmap script
        importmap_scripts = [s for s in scripts if s.type == ScriptType.IMPORTMAP]
        assert len(importmap_scripts) == 1
        assert '"lodash"' in importmap_scripts[0].inline


class TestScriptOutput:
    """Tests for script output functions."""
    
    def setup_method(self):
        """Clear scripts before each test."""
        clear_scripts()
    
    def test_get_head_scripts(self):
        """get_head_scripts should return head scripts."""
        Script(src="/js/critical.js", strategy="beforeInteractive", preload=True)
        
        head = get_head_scripts()
        
        assert 'src="/js/critical.js"' in head
    
    def test_get_body_scripts(self):
        """get_body_scripts should return body scripts."""
        Script(src="/js/app.js", strategy="afterInteractive")
        
        body = get_body_scripts()
        
        assert 'src="/js/app.js"' in body


class TestZeroJSWrapper:
    """Tests verifying zero JS wrapper overhead."""
    
    def test_no_wrapper_js(self):
        """Script component should use native attributes, no wrapper."""
        clear_scripts()
        
        Script(src="/js/app.js")
        
        registry = get_script_registry()
        html = registry.get_body_scripts()
        
        # Should use native defer, not a JS loader
        if html:
            assert "defer" in html
            # No wrapper function
            assert "loadScript" not in html
    
    def test_lazy_minimal_js(self):
        """Lazy scripts should use minimal loader."""
        clear_scripts()
        
        Script(src="/js/lazy.js", strategy="lazyOnload")
        
        registry = get_script_registry()
        lazy_html = registry.get_lazy_scripts()
        
        if lazy_html:
            # Should use requestIdleCallback or simple loader
            assert "requestIdleCallback" in lazy_html or "setTimeout" in lazy_html

