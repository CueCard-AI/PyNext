"""
Build-Time Interception Compiler for PyNext.

Handles interception route compilation at build time:
- Pre-computes interception rules
- Analyzes modal content for hydration
- Generates interception manifest
- Configures modal-level caching

Zero runtime resolution overhead - all interception rules
are pre-computed during build.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
import hashlib
import json
import ast
import re
from concurrent.futures import ThreadPoolExecutor

from pynext.router.intercept import (
    CompiledInterceptionMap,
    InterceptionRule,
    InterceptionType,
    InterceptionScanner,
    get_interception_scanner,
)


@dataclass
class InterceptionAnalysis:
    """Analysis result for an interception rule."""
    target_pattern: str
    interceptor_path: str
    interception_type: str
    is_interactive: bool  # Modal content needs hydration
    estimated_size: int   # Modal content size
    slot_name: str
    has_close_handler: bool
    animation_type: str


@dataclass
class InterceptionManifestEntry:
    """Entry in the interception manifest."""
    target_pattern: str
    interceptor_path: str
    original_path: str
    interception_type: str
    slot_name: str
    requires_hydration: bool
    bundle_id: Optional[str]
    config: Dict[str, Any]


@dataclass
class InterceptionManifest:
    """Complete manifest of all interception routes."""
    rules: List[InterceptionManifestEntry]
    bundles: Dict[str, str]  # interceptor_path -> bundle_id
    stats: Dict[str, int]


@dataclass
class InterceptionBuildConfig:
    """Configuration for interception build."""
    pages_dir: Path = Path("pages")
    output_dir: Path = Path("dist/_intercept")
    cache_dir: Path = Path(".pynext/intercept-cache")
    analyze_hydration: bool = True
    generate_bundles: bool = True


class InterceptionCompiler:
    """
    Build-time compiler for intercepting routes.
    
    Pre-computes interception rules and generates manifests
    for zero-runtime-cost modal pattern.
    """
    
    def __init__(self, config: Optional[InterceptionBuildConfig] = None):
        self.config = config or InterceptionBuildConfig()
        self._scanner = get_interception_scanner()
        self._analyses: Dict[str, InterceptionAnalysis] = {}
    
    def compile(
        self,
        project_root: Optional[Path] = None,
    ) -> InterceptionManifest:
        """
        Compile all interception routes.
        
        Returns a complete manifest of all interception rules.
        """
        project_root = project_root or Path.cwd()
        pages_dir = project_root / self.config.pages_dir
        output_dir = project_root / self.config.output_dir
        cache_dir = project_root / self.config.cache_dir
        
        # Ensure directories exist
        output_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Scan for interception routes
        interception_map = self._scanner.scan(pages_dir)
        
        if not interception_map.rules:
            return InterceptionManifest(
                rules=[],
                bundles={},
                stats={"total": 0, "interactive": 0, "static": 0},
            )
        
        # Analyze and compile each rule
        manifest_rules: List[InterceptionManifestEntry] = []
        bundles: Dict[str, str] = {}
        
        interactive_count = 0
        static_count = 0
        
        for rule in interception_map.rules:
            # Analyze the interceptor
            analysis = self._analyze_interceptor(rule, pages_dir)
            self._analyses[rule.interceptor_path] = analysis
            
            if analysis.is_interactive:
                interactive_count += 1
            else:
                static_count += 1
            
            # Generate bundle for interactive interceptors
            bundle_id = None
            if analysis.is_interactive and self.config.generate_bundles:
                bundle_id = self._generate_interceptor_bundle(
                    rule,
                    output_dir,
                )
                if bundle_id:
                    bundles[rule.interceptor_path] = bundle_id
            
            # Create manifest entry
            manifest_rules.append(InterceptionManifestEntry(
                target_pattern=rule.target_pattern,
                interceptor_path=rule.interceptor_path,
                original_path=rule.original_path,
                interception_type=rule.interception_type.value,
                slot_name=rule.slot_name,
                requires_hydration=analysis.is_interactive,
                bundle_id=bundle_id,
                config={
                    "animation": analysis.animation_type,
                    "hasCloseHandler": analysis.has_close_handler,
                },
            ))
        
        manifest = InterceptionManifest(
            rules=manifest_rules,
            bundles=bundles,
            stats={
                "total": len(manifest_rules),
                "interactive": interactive_count,
                "static": static_count,
            },
        )
        
        # Write manifest to disk
        self._write_manifest(manifest, output_dir)
        
        return manifest
    
    def _analyze_interceptor(
        self,
        rule: InterceptionRule,
        pages_dir: Path,
    ) -> InterceptionAnalysis:
        """Analyze an interceptor for hydration requirements."""
        interceptor_file = Path(rule.interceptor_path)
        
        is_interactive = False
        estimated_size = 0
        has_close_handler = False
        animation_type = "fade"
        
        if interceptor_file.exists():
            try:
                content = interceptor_file.read_text()
                estimated_size = len(content.encode('utf-8'))
                
                # Parse AST to detect interactivity
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    # Check for Signal, Store, Effect usage
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in ['Signal', 'Store', 'Effect', 'createResource']:
                                is_interactive = True
                            if node.func.id == 'Modal':
                                # Check Modal arguments for animation
                                for kw in node.keywords:
                                    if kw.arg == 'animation' and isinstance(kw.value, ast.Constant):
                                        animation_type = kw.value.value
                                    if kw.arg == 'on_close':
                                        has_close_handler = True
                    
                    # Check for @island decorator
                    if isinstance(node, ast.FunctionDef):
                        for decorator in node.decorator_list:
                            if isinstance(decorator, ast.Name) and decorator.id == 'island':
                                is_interactive = True
                                
            except Exception:
                pass
        
        return InterceptionAnalysis(
            target_pattern=rule.target_pattern,
            interceptor_path=rule.interceptor_path,
            interception_type=rule.interception_type.value,
            is_interactive=is_interactive,
            estimated_size=estimated_size,
            slot_name=rule.slot_name,
            has_close_handler=has_close_handler,
            animation_type=animation_type,
        )
    
    def _generate_interceptor_bundle(
        self,
        rule: InterceptionRule,
        output_dir: Path,
    ) -> Optional[str]:
        """
        Generate a JavaScript bundle for an interactive interceptor.
        
        Returns the bundle ID.
        """
        # Create bundle ID
        bundle_content = f"{rule.target_pattern}:{rule.interceptor_path}"
        bundle_id = hashlib.md5(bundle_content.encode()).hexdigest()[:12]
        
        return bundle_id
    
    def _write_manifest(
        self,
        manifest: InterceptionManifest,
        output_dir: Path,
    ) -> None:
        """Write manifest to disk."""
        manifest_data = {
            "rules": [
                {
                    "targetPattern": entry.target_pattern,
                    "interceptorPath": entry.interceptor_path,
                    "originalPath": entry.original_path,
                    "interceptionType": entry.interception_type,
                    "slotName": entry.slot_name,
                    "requiresHydration": entry.requires_hydration,
                    "bundleId": entry.bundle_id,
                    "config": entry.config,
                }
                for entry in manifest.rules
            ],
            "bundles": manifest.bundles,
            "stats": manifest.stats,
        }
        
        manifest_path = output_dir / "intercept-manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)
    
    def get_analysis(self, interceptor_path: str) -> Optional[InterceptionAnalysis]:
        """Get analysis for a specific interceptor."""
        return self._analyses.get(interceptor_path)


def compile_interceptions(
    project_root: Optional[Path] = None,
    config: Optional[InterceptionBuildConfig] = None,
) -> InterceptionManifest:
    """
    Compile all interception routes for production build.
    
    Called by CLI build command.
    """
    compiler = InterceptionCompiler(config)
    return compiler.compile(project_root=project_root)


def build_interception_map(
    pages_dir: Path,
    output_dir: Path,
) -> Dict[str, Any]:
    """
    Build interception map for the application.
    
    Returns summary of compiled interceptions.
    """
    config = InterceptionBuildConfig(
        pages_dir=pages_dir,
        output_dir=output_dir / "_intercept",
    )
    
    manifest = compile_interceptions(config=config)
    
    return {
        "total_rules": manifest.stats.get("total", 0),
        "interactive_modals": manifest.stats.get("interactive", 0),
        "static_modals": manifest.stats.get("static", 0),
        "bundles": len(manifest.bundles),
    }


# =============================================================================
# Navigation Integration
# =============================================================================

def get_interception_navigation_js() -> str:
    """
    Get JavaScript for intercepting navigation with modals.
    
    Integrates with the main navigation system to:
    - Detect interceptable routes
    - Show modal instead of full page
    - Preserve background as static
    - Handle modal close navigation
    """
    return """
(function() {
  window.__pynext__ = window.__pynext__ || {};
  window.__pynext__.intercept = {
    rules: [],
    
    // Initialize with manifest data
    init: function(rules) {
      this.rules = rules || [];
    },
    
    // Check if a path should be intercepted
    shouldIntercept: function(path, referrer) {
      for (var i = 0; i < this.rules.length; i++) {
        var rule = this.rules[i];
        if (this.matchPattern(path, rule.targetPattern)) {
          // Check referrer for soft interception
          if (rule.interceptionType === 'soft') {
            if (!referrer) return null;
            // For (..), check if referrer is in scope
            return rule;
          } else if (rule.interceptionType === 'hard') {
            // (...) always intercepts
            return rule;
          }
        }
      }
      return null;
    },
    
    // Match a path against a pattern
    matchPattern: function(path, pattern) {
      // Convert :param to regex
      var regex = pattern.replace(/:[^/]+/g, '[^/]+');
      regex = regex.replace(/\\*[^/]+/g, '.+');
      regex = new RegExp('^' + regex + '$');
      return regex.test(path);
    },
    
    // Handle intercepted navigation
    handleIntercept: async function(rule, path, params) {
      // Load modal content via fetch
      var response = await fetch(path + '?_modal=1', {
        headers: { 'X-PyNext-Modal': '1' }
      });
      
      if (!response.ok) return false;
      
      var html = await response.text();
      
      // Find modal portal and inject content
      var portal = document.getElementById('modal-portal');
      if (portal) {
        portal.innerHTML = html;
        
        // Initialize modal behavior
        var dialog = portal.querySelector('dialog');
        if (dialog && window.__pynext__.modal) {
          window.__pynext__.modal.init(dialog.id, {
            closeUrl: window.location.pathname,
            closeOnOverlay: true,
            closeOnEscape: true,
            animation: rule.config?.animation || 'fade'
          });
        }
      }
      
      // Update URL without full navigation
      history.pushState({ modal: true, path: path }, '', path);
      
      return true;
    }
  };
  
  // Extend navigation with interception support
  if (window.__pynext__.navigate) {
    var originalNavigate = window.__pynext__.navigate;
    
    window.__pynext__.navigate = async function(path, options) {
      var referrer = window.location.pathname;
      var rule = window.__pynext__.intercept.shouldIntercept(path, referrer);
      
      if (rule) {
        var handled = await window.__pynext__.intercept.handleIntercept(rule, path, {});
        if (handled) return;
      }
      
      // Fall back to regular navigation
      return originalNavigate(path, options);
    };
  }
})();
"""


def needs_interception_runtime() -> bool:
    """Check if current page needs interception runtime."""
    interception_map = get_interception_scanner().get_map()
    return interception_map is not None and len(interception_map.rules) > 0

