"""
Command-line interface for PyNext.

Provides commands for development, building, and project initialization.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def cmd_dev(args: argparse.Namespace) -> int:
    """Run the development server."""
    from pynext.server.dev import run_dev_server
    from pynext.deps import DependencyManager
    
    # Check dependencies on startup (unless --skip-deps)
    if not args.skip_deps:
        deps = DependencyManager(".")
        if deps.has_dependencies():
            missing = deps.check_all()
            if missing["python"] or missing["npm"]:
                print("[PyNext] Checking dependencies...")
                deps.print_status()
                if not args.no_install:
                    print("[PyNext] Installing missing dependencies...")
                    deps.install_all()
    
    run_dev_server(
        pages_dir=args.pages,
        static_dir=args.static,
        host=args.host,
        port=args.port,
    )
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    """Build for production."""
    import asyncio
    from pynext.bundler.npm import get_bundler
    from pynext.router.file_router import FileRouter
    
    print("[PyNext] Building for production...")
    
    # Bundle npm packages
    bundler = get_bundler()
    bundler.project_dir = Path(args.dir).resolve()
    bundler.output_dir = Path(args.output).resolve() / "bundles"
    bundles = bundler.bundle_all()
    
    if bundles:
        print(f"[PyNext] Bundled {len(bundles)} npm packages")
    
    # Process images (build-time optimization)
    try:
        from pynext.bundler.images import process_images_for_build
        
        static_path = Path(args.static).resolve()
        image_output = Path(args.output).resolve() / "_next" / "image"
        
        print("[PyNext] Processing images...")
        result = asyncio.run(process_images_for_build(
            source_dir=static_path,
            output_dir=image_output,
        ))
        
        if result["total"] > 0:
            print(f"[PyNext] Processed {result['successful']}/{result['total']} images")
            if result["zero_js_pages"] if "zero_js_pages" in result else 0:
                print(f"[PyNext]   → Zero JS images: {result.get('zero_js_pages', 'all')}")
            if result["errors"]:
                for err in result["errors"]:
                    print(f"[PyNext]   ⚠ {err['src']}: {err['error']}")
    except ImportError:
        print("[PyNext] Image processing skipped (Pillow not installed)")
    except Exception as e:
        print(f"[PyNext] Image processing error: {e}")
    
    # Scan routes
    router = FileRouter(args.pages)
    router.scan()
    print(f"[PyNext] Found {len(router.routes)} routes")
    
    # Copy static files
    static_dir = Path(args.static)
    output_static = Path(args.output) / "static"
    if static_dir.exists():
        import shutil
        if output_static.exists():
            shutil.rmtree(output_static)
        shutil.copytree(static_dir, output_static)
        print(f"[PyNext] Copied static files")
    
    # Static Site Generation (SSG)
    try:
        from pynext.bundler.static import build_static_site
        
        print("[PyNext] Generating static pages...")
        ssg_result = asyncio.run(build_static_site(
            pages_dir=Path(args.pages).resolve(),
            output_dir=Path(args.output).resolve(),
            static_dir=Path(args.static).resolve(),
        ))
        
        if ssg_result.total_pages > 0:
            print(f"[PyNext] Generated {ssg_result.total_pages} static pages:")
            print(f"[PyNext]   → Zero JS pages: {ssg_result.zero_js_pages}")
            print(f"[PyNext]   → Hybrid pages (islands): {ssg_result.hybrid_pages}")
            if ssg_result.errors:
                for err in ssg_result.errors:
                    print(f"[PyNext]   ⚠ {err['route']}: {err['error']}")
    except ImportError as e:
        print(f"[PyNext] SSG skipped: {e}")
    except Exception as e:
        print(f"[PyNext] SSG error: {e}")
    
    # Partial Prerendering (PPR) Analysis
    try:
        from pynext.bundler.ppr import analyze_ppr_for_build, PPRBuildConfig
        
        print("[PyNext] Analyzing PPR boundaries...")
        ppr_config = PPRBuildConfig(
            output_dir=Path(args.output).resolve() / ".pynext" / "ppr-cache",
        )
        ppr_results = analyze_ppr_for_build(
            pages_dir=Path(args.pages).resolve(),
            project_root=Path(args.dir).resolve(),
            config=ppr_config,
        )
        
        if ppr_results:
            fully_static = sum(1 for p in ppr_results.values() if p.is_fully_static)
            hybrid = sum(1 for p in ppr_results.values() if p.has_dynamic_parts)
            print(f"[PyNext] Analyzed {len(ppr_results)} pages for PPR:")
            print(f"[PyNext]   → Fully static (zero hydration): {fully_static}")
            print(f"[PyNext]   → Hybrid (static shell + dynamic holes): {hybrid}")
            print(f"[PyNext]   → Component-level granularity enabled")
    except ImportError as e:
        print(f"[PyNext] PPR analysis skipped: {e}")
    except Exception as e:
        print(f"[PyNext] PPR analysis error: {e}")
    
    # Font Optimization (build-time processing)
    try:
        from pynext.bundler.fonts import process_fonts_for_build, FontProcessorConfig
        
        print("[PyNext] Processing fonts...")
        font_config = FontProcessorConfig(
            output_dir=Path(args.output).resolve() / "_next" / "fonts",
            cache_dir=Path(args.dir).resolve() / ".pynext" / "font-cache",
        )
        fonts = process_fonts_for_build(
            project_root=Path(args.dir).resolve(),
            config=font_config,
        )
        
        if fonts:
            print(f"[PyNext] Processed {len(fonts)} fonts:")
            print(f"[PyNext]   → Zero JS overhead (pure CSS)")
            print(f"[PyNext]   → Precomputed size-adjust for no layout shift")
    except ImportError as e:
        print(f"[PyNext] Font processing skipped: {e}")
    except Exception as e:
        print(f"[PyNext] Font processing error: {e}")
    
    # Script Optimization (build-time analysis)
    try:
        from pynext.bundler.scripts import optimize_scripts_for_build, ScriptOptimizerConfig
        
        print("[PyNext] Analyzing scripts...")
        script_config = ScriptOptimizerConfig(
            output_dir=Path(args.output).resolve() / "_next" / "scripts",
            cache_dir=Path(args.dir).resolve() / ".pynext" / "script-cache",
        )
        script_analyses = optimize_scripts_for_build(
            project_root=Path(args.dir).resolve(),
            config=script_config,
        )
        
        if script_analyses:
            print(f"[PyNext] Analyzed {len(script_analyses)} scripts:")
            print(f"[PyNext]   → Zero wrapper overhead")
            print(f"[PyNext]   → Native loading strategies")
    except ImportError as e:
        print(f"[PyNext] Script analysis skipped: {e}")
    except Exception as e:
        print(f"[PyNext] Script analysis error: {e}")
    
    # Parallel Routes Compilation (build-time slot resolution)
    try:
        from pynext.bundler.parallel import build_parallel_routes_map
        
        print("[PyNext] Compiling parallel routes...")
        parallel_result = build_parallel_routes_map(
            pages_dir=Path(args.pages).resolve(),
            output_dir=Path(args.output).resolve(),
        )
        
        if parallel_result["total_slots"] > 0:
            print(f"[PyNext] Compiled {parallel_result['total_slots']} parallel slots:")
            print(f"[PyNext]   → Static slots: {parallel_result['static_slots']}")
            print(f"[PyNext]   → Interactive slots: {parallel_result['interactive_slots']}")
            print(f"[PyNext]   → Slot-level caching enabled")
    except ImportError as e:
        print(f"[PyNext] Parallel routes skipped: {e}")
    except Exception as e:
        print(f"[PyNext] Parallel routes error: {e}")
    
    # Intercepting Routes Compilation (modal pattern)
    try:
        from pynext.bundler.intercept import build_interception_map
        
        print("[PyNext] Compiling intercepting routes...")
        intercept_result = build_interception_map(
            pages_dir=Path(args.pages).resolve(),
            output_dir=Path(args.output).resolve(),
        )
        
        if intercept_result["total_rules"] > 0:
            print(f"[PyNext] Compiled {intercept_result['total_rules']} interception rules:")
            print(f"[PyNext]   → Static modals: {intercept_result['static_modals']}")
            print(f"[PyNext]   → Interactive modals: {intercept_result['interactive_modals']}")
            print(f"[PyNext]   → Background preserved as static")
    except ImportError as e:
        print(f"[PyNext] Interception routes skipped: {e}")
    except Exception as e:
        print(f"[PyNext] Interception routes error: {e}")
    
    # Generate route manifest
    manifest = {
        "routes": router.get_routes_info(),
        "bundles": {name: str(path) for name, path in bundles.items()},
    }
    
    manifest_path = Path(args.output) / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    print(f"[PyNext] Build complete: {args.output}")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a new PyNext project."""
    from pynext.core.paths import ensure_structure
    
    project_dir = Path(args.name).resolve()
    
    if project_dir.exists() and any(project_dir.iterdir()):
        print(f"Error: Directory {args.name} already exists and is not empty")
        return 1
    
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine if using src/ structure
    use_src = getattr(args, 'src', False)
    if not use_src and not getattr(args, 'yes', False):
        # Ask about structure (interactive mode)
        try:
            response = input("Use src/ directory structure? [y/N]: ").strip().lower()
            use_src = response in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            use_src = False
    
    # Create directory structure using paths module
    paths = ensure_structure(project_dir, use_src=use_src)
    pages_dir = paths.pages
    components_dir = paths.components
    
    structure_type = "src/" if use_src else "standard"
    print(f"[PyNext] Creating project with {structure_type} structure...")
    
    # Create index page
    index_page = '''"""
PyNext - Home Page
"""

from pynext import page, Signal, div, h1, p, button, span


@page(title="Welcome to PyNext")
def index():
    count = Signal(0)
    
    return div(class_="container")[
        h1()["Welcome to PyNext! 🚀"],
        p()["A Python framework with SolidJS-inspired reactivity"],
        
        div(class_="counter")[
            p()[
                "Count: ",
                span()[count]
            ],
            button(onclick=lambda: count.update(lambda x: x + 1))[
                "Increment"
            ]
        ]
    ]
'''
    (pages_dir / "index.py").write_text(index_page)
    
    # Create about page
    about_page = '''"""
PyNext - About Page
"""

from pynext import page, div, h1, p, a


@page(title="About PyNext")
def about():
    return div(class_="container")[
        h1()["About PyNext"],
        p()[
            "PyNext is a Python web framework that combines the best of Next.js "
            "and SolidJS, providing file-based routing, fine-grained reactivity, "
            "and seamless Python integration."
        ],
        p()[
            a(href="/")["← Back to Home"]
        ]
    ]
'''
    (pages_dir / "about.py").write_text(about_page)
    
    # Create dynamic route example
    user_page = '''"""
PyNext - Dynamic Route Example
"""

from pynext import page, div, h1, p, a, get_params


@page(title="User Profile")
def user_profile(id: str = ""):
    params = get_params()
    user_id = params.get("id", id)
    
    return div(class_="container")[
        h1()[f"User Profile: {user_id}"],
        p()["This is a dynamic route example."],
        p()[
            a(href="/")["← Back to Home"]
        ]
    ]
'''
    (pages_dir / "users").mkdir()
    (pages_dir / "users" / "[id].py").write_text(user_page)
    
    # Create server action example
    action_page = '''"""
PyNext - Server Actions Example
"""

from pynext import page, server_action, div, h1, p, button, pre
import json
import os


@server_action
async def get_system_info() -> dict:
    """Server action that returns system information."""
    return {
        "python_version": os.sys.version,
        "platform": os.sys.platform,
        "cwd": os.getcwd(),
    }


@page(title="Server Actions")
def actions():
    return div(class_="container")[
        h1()["Server Actions"],
        p()["Click the button to call a server action:"],
        button(onclick=get_system_info)["Get System Info"],
        pre(id="result")["Results will appear here..."]
    ]
'''
    (pages_dir / "actions.py").write_text(action_page)
    
    # Create config file
    config = '''"""
PyNext Configuration
"""

# Build options
build = {
    "output": ".pynext/build",
    "minify": True,
}

# Development options
dev = {
    "port": 3000,
    "host": "127.0.0.1",
}
'''
    (project_dir / "pynext.config.py").write_text(config)
    
    # Create dependency files
    from pynext.deps import create_dependency_templates
    create_dependency_templates(str(project_dir))
    
    # Create base CSS
    base_css = '''/* PyNext Base Styles */

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 20px;
}

h1 {
    color: #1a1a2e;
    margin-bottom: 20px;
}

p {
    color: #4a4a6a;
    margin-bottom: 16px;
}

button {
    background: #6366f1;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    transition: background 0.2s;
}

button:hover {
    background: #4f46e5;
}

.counter {
    background: #f8f9fa;
    padding: 24px;
    border-radius: 12px;
    margin-top: 20px;
}

a {
    color: #6366f1;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

pre {
    background: #1a1a2e;
    color: #e2e8f0;
    padding: 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin-top: 16px;
}
'''
    (project_dir / "public" / "styles.css").write_text(base_css)
    
    # Create .gitignore
    gitignore = '''# PyNext
.pynext/
__pycache__/
*.pyc
.env

# Node
node_modules/
package-lock.json

# IDE
.vscode/
.idea/
'''
    (project_dir / ".gitignore").write_text(gitignore)
    
    print(f"""
  ✨ Created PyNext project: {args.name}

  Next steps:
  
    cd {args.name}
    pip install pynext
    pynext dev

  Project structure:
  
    {args.name}/
    ├── pages/
    │   ├── index.py              # Home page
    │   ├── about.py              # About page
    │   ├── actions.py            # Server actions example
    │   └── users/
    │       └── [id].py           # Dynamic route
    ├── public/
    │   └── styles.css            # Base styles
    ├── components/               # Reusable components
    ├── pynext.config.py          # Configuration
    ├── pynext.requirements.txt   # Python dependencies
    └── pynext.npm.txt            # NPM dependencies
""")
    
    return 0


def cmd_routes(args: argparse.Namespace) -> int:
    """List all registered routes."""
    from pynext.router.file_router import FileRouter
    
    router = FileRouter(args.pages)
    router.scan()
    
    if not router.routes:
        print("No routes found.")
        return 0
    
    print("\nRegistered Routes:\n")
    for route in router.routes:
        print(f"  {route.pattern.url_pattern:<30} → {route.module_path}")
    print()
    
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    """
    Generate components, pages, APIs, and more.
    
    Supports:
    - Interactive mode (default): prompts for options
    - AI mode (--ai): uses Anthropic Claude with leading questions
    - Non-interactive (--yes): uses defaults without prompts
    
    Example:
        pynext g page blog            # Interactive
        pynext g page blog --yes      # Non-interactive
        pynext g page blog --ai       # AI-assisted
    """
    from pathlib import Path
    from pynext.generator import Generator
    from pynext.generator.prompts import prompt_for_type
    from pynext.generator.ai import ai_interview, generate_with_ai, generate_quick
    from pynext.generator.validators import ValidationError
    
    gen = Generator(Path.cwd())
    
    try:
        # AI mode with direct prompt
        if args.ai and args.prompt:
            print(f"\n🤖 Generating {args.type}: {args.name}")
            print(f"   Prompt: {args.prompt}\n")
            
            content = generate_quick(
                args.type,
                args.name,
                args.prompt,
                api_key=args.api_key,
            )
            path = gen.create_from_content(
                args.type,
                args.name,
                content,
                force=args.force,
            )
            
        # AI mode with interview
        elif args.ai:
            answers = ai_interview(
                args.type,
                args.name,
                api_key=args.api_key,
            )
            
            if not answers:
                print("\n❌ No answers provided. Aborting.")
                return 1
            
            content = generate_with_ai(
                args.type,
                args.name,
                answers,
                api_key=args.api_key,
            )
            path = gen.create_from_content(
                args.type,
                args.name,
                content,
                force=args.force,
            )
            
        # Interactive mode (default)
        elif not args.yes:
            props = prompt_for_type(args.type, args.name)
            path = gen.create(
                args.type,
                args.name,
                template_style=args.template_style,
                props=props,
                force=args.force,
            )
            
        # Non-interactive mode
        else:
            path = gen.create(
                args.type,
                args.name,
                template_style=args.template_style,
                force=args.force,
            )
        
        # Show result
        relative_path = path.relative_to(Path.cwd())
        print(f"\n✅ Created: {relative_path}\n")
        
        # Show helpful next steps
        if args.type == "page":
            route = args.name.replace("_", "-")
            print(f"   → View at: http://localhost:3000/{route}")
        elif args.type in ("component", "island"):
            print(f"   → Import: from components.{args.name} import {args.name}")
        elif args.type == "api":
            route = args.name.replace("_", "-")
            print(f"   → Endpoint: http://localhost:3000/api/{route}")
        elif args.type == "action":
            print(f"   → Import: from actions.{args.name} import {args.name}")
        elif args.type == "hook":
            print(f"   → Import: from hooks.{args.name} import {args.name}")
        
        return 0
        
    except ValidationError as e:
        print(f"\n❌ Validation error: {e}")
        return 1
    except FileExistsError as e:
        print(f"\n❌ {e}")
        return 1
    except ValueError as e:
        print(f"\n❌ {e}")
        return 1
    except ImportError as e:
        print(f"\n❌ {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


def cmd_ui(args: argparse.Namespace) -> int:
    """Manage UI components (Tier 2: Official components)."""
    from pynext.registry import (
        list_available_components,
        copy_component_to_project,
        AVAILABLE_COMPONENTS,
    )
    from pynext.registry.components import copy_all_components
    
    project_dir = Path(args.dir).resolve()
    
    if args.ui_command == "add":
        components = args.components
        
        # Handle --all flag
        if args.all:
            print("[PyNext] Copying all UI components...")
            copied = copy_all_components(project_dir)
            print(f"[PyNext] Copied {len(copied)} components to components/ui/")
            for path in copied:
                print(f"  ✓ {path.name}")
            return 0
        
        if not components:
            print("Error: Specify component names or use --all")
            print("Example: pynext ui add button card dialog")
            return 1
        
        # Copy specified components
        copied = []
        failed = []
        for name in components:
            if name not in AVAILABLE_COMPONENTS:
                failed.append(name)
                continue
            
            result = copy_component_to_project(name, project_dir)
            if result:
                copied.append(result)
                print(f"  ✓ {name} → {result.relative_to(project_dir)}")
            else:
                failed.append(name)
        
        if copied:
            print(f"\n[PyNext] Copied {len(copied)} component(s)")
        
        if failed:
            print(f"\n[PyNext] Failed to copy: {', '.join(failed)}")
            print("  Available components: " + ", ".join(AVAILABLE_COMPONENTS.keys()))
            return 1
        
        return 0
    
    elif args.ui_command == "list":
        print("\n[PyNext] Available UI Components\n")
        
        # Group by category
        categories = {}
        for comp in list_available_components():
            if comp.category not in categories:
                categories[comp.category] = []
            categories[comp.category].append(comp)
        
        for category, components in sorted(categories.items()):
            print(f"  {category.upper()}")
            for comp in components:
                exports = ", ".join(comp.exports[:3])
                if len(comp.exports) > 3:
                    exports += f" (+{len(comp.exports) - 3} more)"
                print(f"    {comp.name:<20} {exports}")
            print()
        
        print(f"  Total: {len(AVAILABLE_COMPONENTS)} components")
        print("\n  Usage: pynext ui add <component> [component...]")
        print("         pynext ui add --all")
        return 0
    
    else:
        # No subcommand, show help
        print("\n[PyNext] UI Component Management")
        print("\n  Commands:")
        print("    pynext ui list              List available components")
        print("    pynext ui add <names...>    Copy components for customization")
        print("    pynext ui add --all         Copy all components")
        print("\n  Components are copied to components/ui/ for editing")
        print("  Or import directly: from pynext.shadcn import Button")
        return 0


def cmd_registry(args: argparse.Namespace) -> int:
    """Manage custom component registries (Tier 3)."""
    from pynext.registry import RegistryManager
    
    manager = RegistryManager(args.dir)
    
    if args.registry_command == "add":
        if not args.url:
            print("Error: --url is required")
            print("Example: pynext registry add acme-ui --url=https://ui.acme.com")
            print("         pynext registry add my-lib --url=github:user/repo")
            return 1
        
        print(f"[PyNext] Adding registry: {args.name}")
        registry = manager.add_registry(args.name, args.url)
        print(f"  ✓ Added {registry.name}")
        print(f"  URL: {registry.url}")
        
        if registry.components:
            print(f"  Components: {len(registry.components)}")
        else:
            print("  Note: Registry metadata will be fetched on first install")
        
        return 0
    
    elif args.registry_command == "remove":
        if manager.remove_registry(args.name):
            print(f"[PyNext] Removed registry: {args.name}")
            return 0
        else:
            print(f"Error: Registry not found: {args.name}")
            return 1
    
    elif args.registry_command == "list":
        registries = manager.list_registries()
        
        if not registries:
            print("\n[PyNext] No custom registries configured")
            print("\n  Add one with: pynext registry add <name> --url=<url>")
            return 0
        
        print("\n[PyNext] Custom Registries\n")
        for reg in registries:
            print(f"  {reg.name}")
            print(f"    URL: {reg.url}")
            print(f"    Version: {reg.version}")
            if reg.components:
                print(f"    Components: {', '.join(reg.components.keys())}")
            print()
        
        return 0
    
    elif args.registry_command == "install":
        # Parse registry:component format
        if ":" not in args.component:
            print("Error: Use format registry:component")
            print("Example: pynext registry install acme-ui:data-table")
            return 1
        
        registry_name, component_name = args.component.split(":", 1)
        
        try:
            print(f"[PyNext] Installing {component_name} from {registry_name}...")
            installed = manager.install_component(registry_name, component_name)
            print(f"  ✓ Installed {len(installed)} file(s)")
            for path in installed:
                print(f"    {path.relative_to(manager.project_dir)}")
            return 0
        except ValueError as e:
            print(f"Error: {e}")
            return 1
    
    elif args.registry_command == "init":
        from pynext.registry.manager import create_registry_template
        
        output_path = Path(args.dir) / "pynext-registry.json"
        create_registry_template(output_path)
        print(f"[PyNext] Created {output_path}")
        print("  Edit this file to define your component library")
        return 0
    
    else:
        # No subcommand, show help
        print("\n[PyNext] Custom Registry Management")
        print("\n  Commands:")
        print("    pynext registry list                      List registered sources")
        print("    pynext registry add <name> --url=<url>    Add a custom registry")
        print("    pynext registry remove <name>             Remove a registry")
        print("    pynext registry install <reg>:<comp>      Install from registry")
        print("    pynext registry init                      Create registry template")
        print("\n  URL formats:")
        print("    https://ui.example.com                    HTTP URL")
        print("    github:owner/repo                         GitHub repository")
        return 0


def cmd_deps(args: argparse.Namespace) -> int:
    """Manage project dependencies."""
    from pynext.deps import DependencyManager
    
    deps = DependencyManager(args.dir)
    
    if args.deps_command == "install":
        print("[PyNext] Installing dependencies...")
        
        if args.python_only:
            success = deps.install_python_deps()
            if success:
                print("[PyNext] Python dependencies installed ✓")
            else:
                print("[PyNext] Failed to install Python dependencies")
                return 1
        elif args.npm_only:
            success = deps.install_npm_deps()
            if success:
                print("[PyNext] NPM dependencies installed ✓")
            else:
                print("[PyNext] Failed to install NPM dependencies")
                return 1
        else:
            python_ok = deps.install_python_deps()
            npm_ok = deps.install_npm_deps()
            
            if python_ok:
                print("[PyNext] Python dependencies installed ✓")
            if npm_ok:
                print("[PyNext] NPM dependencies installed ✓")
            
            if not python_ok or not npm_ok:
                return 1
        
        return 0
    
    elif args.deps_command == "check":
        print("[PyNext] Checking dependencies...")
        
        missing = deps.check_all()
        
        if not missing["python"] and not missing["npm"]:
            print("[PyNext] All dependencies installed ✓")
            return 0
        
        if missing["python"]:
            print(f"\n[PyNext] Missing Python packages ({len(missing['python'])}):")
            for pkg in missing["python"]:
                print(f"  - {pkg}")
        
        if missing["npm"]:
            print(f"\n[PyNext] Missing NPM packages ({len(missing['npm'])}):")
            for pkg in missing["npm"]:
                print(f"  - {pkg}")
        
        print("\n[PyNext] Run 'pynext deps install' to install missing dependencies")
        return 1
    
    elif args.deps_command == "init":
        from pynext.deps import create_dependency_templates
        
        python_path, npm_path = create_dependency_templates(args.dir)
        print(f"[PyNext] Created {python_path.name}")
        print(f"[PyNext] Created {npm_path.name}")
        return 0
    
    else:
        # No subcommand, show status
        deps.print_status()
        return 0


def cmd_env(args: argparse.Namespace) -> int:
    """Handle env subcommands."""
    from pathlib import Path
    from pynext.env.loader import load_env_files, get_env_files_info
    from pynext.env.schema import load_schema
    from pynext.env.client import get_public_vars
    
    root = Path(getattr(args, "dir", ".")).resolve()
    
    if args.env_command == "list":
        mode = getattr(args, "mode", "development")
        env_vars = load_env_files(root, mode)
        schema = load_schema(root)
        
        if getattr(args, "public", False):
            # Filter to only public vars
            public = get_public_vars(env_vars)
            env_vars = {f"PYNEXT_PUBLIC_{k}": v for k, v in public.items()}
        
        print(f"\n[PyNext] Environment Variables ({len(env_vars)} loaded, mode={mode}):\n")
        
        for key in sorted(env_vars.keys()):
            value = env_vars[key]
            
            # Mask secrets
            is_secret = False
            if schema and key in schema.vars:
                is_secret = schema.vars[key].secret
            elif any(s in key.lower() for s in ["secret", "password", "key", "token", "api_key"]):
                is_secret = True
            
            if getattr(args, "show_values", False):
                display_value = "***" if is_secret else value
                # Truncate long values
                if len(display_value) > 60:
                    display_value = display_value[:57] + "..."
                print(f"  {key}={display_value}")
            else:
                print(f"  {key}")
        
        print()
        return 0
    
    elif args.env_command == "check":
        mode = getattr(args, "mode", "development")
        files_info = get_env_files_info(root, mode)
        
        print(f"\n[PyNext] Environment Files (mode={mode}):\n")
        for info in files_info:
            status = "✓" if info["exists"] else "✗"
            vars_info = f"({info['vars']} vars)" if info["exists"] else "(not found)"
            print(f"  {status} {info['name']} {vars_info}")
        
        # Check for schema
        schema = load_schema(root)
        if schema:
            print(f"\n  ✓ env.schema.py found")
            print(f"    → {len(schema.get_required_vars())} required vars")
            print(f"    → {len(schema.get_optional_vars())} optional vars")
        else:
            print(f"\n  ✗ env.schema.py (not found, validation disabled)")
        
        print()
        return 0
    
    elif args.env_command == "validate":
        schema = load_schema(root)
        if not schema:
            print("[PyNext] No env.schema.py found.")
            print("  Create one to enable validation:")
            print()
            print("  # env.schema.py")
            print("  from pynext.env import EnvSchema, Var")
            print()
            print("  schema = EnvSchema(")
            print("      DATABASE_URL=Var(str, required=True),")
            print("      PORT=Var(int, default=8000),")
            print("  )")
            print()
            return 1
        
        mode = getattr(args, "mode", "production")
        env_vars = load_env_files(root, mode)
        result = schema.validate(env_vars)
        
        if result.valid:
            print(f"[PyNext] ✓ Environment valid for {mode}")
            required = len(schema.get_required_vars())
            optional = len(schema.get_optional_vars())
            print(f"  → {required} required vars present")
            print(f"  → {optional} optional vars configured")
            
            if result.warnings:
                print("\n  Warnings:")
                for w in result.warnings:
                    print(f"    - {w}")
            return 0
        else:
            print(f"[PyNext] ✗ Environment validation failed for {mode}:\n")
            for err in result.errors:
                print(f"  {err.key}: {err.message}")
            print()
            print("  Fix these issues in your .env file or environment.")
            return 1
    
    elif args.env_command == "init":
        schema = load_schema(root)
        if not schema:
            print("[PyNext] No env.schema.py found. Create one first.")
            print()
            print("  # env.schema.py")
            print("  from pynext.env import EnvSchema, Var")
            print()
            print("  schema = EnvSchema(")
            print("      DATABASE_URL=Var(str, required=True),")
            print("      PORT=Var(int, default=8000),")
            print("      DEBUG=Var(bool, default=False),")
            print("  )")
            return 1
        
        template = schema.generate_template()
        force = getattr(args, "force", False)
        
        # Create .env.example
        env_example = root / ".env.example"
        if env_example.exists() and not force:
            print(f"[PyNext] .env.example already exists. Use --force to overwrite.")
            return 1
        
        env_example.write_text(template)
        print(f"[PyNext] ✓ Created .env.example")
        
        # Optionally create .env if it doesn't exist
        env_file = root / ".env"
        if not env_file.exists():
            env_file.write_text(template)
            print(f"[PyNext] ✓ Created .env (fill in your values)")
        else:
            print(f"[PyNext] ℹ .env already exists (not modified)")
        
        print()
        print("  Next steps:")
        print("  1. Edit .env with your actual values")
        print("  2. Run: pynext env validate")
        return 0
    
    elif args.env_command == "generate":
        # Generate TypeScript types for public vars
        schema = load_schema(root)
        if not schema:
            print("[PyNext] No env.schema.py found.")
            return 1
        
        from pynext.build.env import generate_env_types
        
        output = getattr(args, "output", None)
        output_path = Path(output) if output else root / "env.d.ts"
        
        types = generate_env_types(root, output_path)
        if types:
            print(f"[PyNext] ✓ Generated {output_path}")
        else:
            print("[PyNext] No PYNEXT_PUBLIC_* vars found in schema")
        return 0
    
    else:
        # No subcommand - show current env status
        mode = "development"
        env_vars = load_env_files(root, mode)
        schema = load_schema(root)
        public_vars = get_public_vars(env_vars)
        
        print(f"\n[PyNext] Environment Status:\n")
        print(f"  Mode: {mode}")
        print(f"  Total vars: {len(env_vars)}")
        print(f"  Public vars (client): {len(public_vars)}")
        print(f"  Schema: {'✓' if schema else '✗ (no validation)'}")
        
        if schema:
            missing = []
            for key, var in schema.vars.items():
                if var.required and key not in env_vars:
                    missing.append(key)
            if missing:
                print(f"\n  ⚠ Missing required vars:")
                for m in missing:
                    print(f"    - {m}")
        
        print(f"\n  Commands:")
        print(f"    pynext env list        List all variables")
        print(f"    pynext env check       Check env files")
        print(f"    pynext env validate    Validate against schema")
        print(f"    pynext env init        Create .env from schema")
        print()
        return 0


# ========================================
# cmd_sitemap - Sitemap generation
# ========================================

def cmd_sitemap(args: argparse.Namespace) -> int:
    """Handle sitemap subcommands."""
    from pathlib import Path
    from pynext.seo.sitemap import SitemapGenerator, clear_sitemap_configs
    from pynext.router.file_router import FileRouter
    
    root = Path(args.dir).resolve() if hasattr(args, "dir") else Path.cwd()
    
    # Find pages directory
    pages_dir = None
    for candidate in ["pages", "src/pages"]:
        if (root / candidate).is_dir():
            pages_dir = root / candidate
            break
    
    if not pages_dir:
        print("[PyNext] Error: No pages/ directory found.")
        return 1
    
    # Get base URL
    base_url = getattr(args, "base_url", None) or "https://example.com"
    if base_url == "https://example.com":
        print("[PyNext] Warning: Using default base URL. Set --base-url for production.")
    
    if args.sitemap_command == "generate":
        # Initialize router
        router = FileRouter(str(pages_dir))
        router.scan()
        
        # Generate sitemap
        generator = SitemapGenerator(router, base_url)
        entries = generator.discover_urls()
        
        if not entries:
            print("[PyNext] No pages with @sitemap decorator found.")
            print("  Add @sitemap() to your page functions:")
            print()
            print("    from pynext import page, sitemap")
            print()
            print("    @sitemap()")
            print("    @page")
            print("    def MyPage():")
            print("        return div('Hello')")
            return 1
        
        # Determine output
        output_dir = Path(getattr(args, "output", None) or root / "public")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write sitemap(s)
        written = generator.write_to_directory(output_dir, entries)
        
        print(f"[PyNext] ✓ Generated sitemap with {len(entries)} URLs")
        for path in written:
            print(f"  → {path.relative_to(root)}")
        
        if generator.needs_index(entries):
            print(f"  ℹ Split into sitemap index (>{SitemapGenerator.MAX_URLS_PER_SITEMAP} URLs)")
        
        return 0
    
    elif args.sitemap_command == "validate":
        # Validate existing sitemap
        sitemap_path = root / "public" / "sitemap.xml"
        
        if not sitemap_path.exists():
            print(f"[PyNext] No sitemap found at {sitemap_path}")
            print("  Run: pynext sitemap generate")
            return 1
        
        import xml.etree.ElementTree as ET
        
        try:
            tree = ET.parse(sitemap_path)
            root_elem = tree.getroot()
            
            # Count URLs
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = root_elem.findall(".//sm:url", ns) or root_elem.findall(".//url")
            
            print(f"[PyNext] ✓ Valid sitemap")
            print(f"  URLs: {len(urls)}")
            
            # Check for common issues
            warnings = []
            for url_elem in urls[:10]:  # Check first 10
                loc = url_elem.find("sm:loc", ns) or url_elem.find("loc")
                if loc is not None and not loc.text.startswith(("http://", "https://")):
                    warnings.append(f"Relative URL found: {loc.text}")
            
            if warnings:
                print(f"\n  ⚠ Warnings:")
                for w in warnings[:5]:
                    print(f"    - {w}")
            
            return 0
            
        except ET.ParseError as e:
            print(f"[PyNext] ✗ Invalid XML: {e}")
            return 1
    
    elif args.sitemap_command == "preview":
        # Preview sitemap entries without generating file
        router = FileRouter(str(pages_dir))
        router.scan()
        
        generator = SitemapGenerator(router, base_url)
        entries = generator.discover_urls()
        
        print(f"[PyNext] Sitemap Preview ({len(entries)} URLs)")
        print()
        
        limit = getattr(args, "limit", 20)
        for entry in entries[:limit]:
            priority_str = f" (priority={entry.priority})" if entry.priority else ""
            print(f"  {entry.loc}{priority_str}")
        
        if len(entries) > limit:
            print(f"  ... and {len(entries) - limit} more")
        
        return 0
    
    else:
        # No subcommand - show help
        print("\n[PyNext] Sitemap Commands:\n")
        print("  pynext sitemap generate     Generate sitemap.xml")
        print("  pynext sitemap validate     Validate existing sitemap")
        print("  pynext sitemap preview      Preview URLs without generating")
        print()
        print("  Options:")
        print("    --base-url URL           Base URL for sitemap")
        print("    --output DIR             Output directory")
        print()
        return 0


# ========================================
# cmd_robots - Robots.txt management
# ========================================

def cmd_robots(args: argparse.Namespace) -> int:
    """Handle robots subcommands."""
    from pathlib import Path
    from pynext.seo.robots import RobotsConfig, RobotsRule, RobotsGenerator
    
    root = Path(args.dir).resolve() if hasattr(args, "dir") else Path.cwd()
    
    # Get base URL
    base_url = getattr(args, "base_url", None) or "https://example.com"
    
    def load_robots_config() -> RobotsConfig:
        """Load robots config from pynext.config.py or default."""
        config_path = root / "pynext.config.py"
        
        if config_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("pynext_config", config_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "robots"):
                    return module.robots
        
        # Default config
        return RobotsConfig(
            rules=[RobotsRule(user_agent="*", allow=["/"]) ],
            sitemap=True,
        )
    
    if args.robots_command == "generate":
        config = load_robots_config()
        generator = RobotsGenerator(config, base_url)
        
        # Validate
        warnings = generator.validate()
        if warnings:
            print("[PyNext] ⚠ Warnings:")
            for w in warnings:
                print(f"  - {w}")
            print()
        
        # Write file
        output_path = Path(getattr(args, "output", None) or root / "public" / "robots.txt")
        generator.write_to_file(output_path)
        
        print(f"[PyNext] ✓ Generated robots.txt")
        print(f"  → {output_path.relative_to(root)}")
        return 0
    
    elif args.robots_command == "preview":
        config = load_robots_config()
        content = config.generate(base_url)
        
        print("[PyNext] Robots.txt Preview:\n")
        print(content)
        print()
        return 0
    
    elif args.robots_command == "validate":
        robots_path = root / "public" / "robots.txt"
        
        if not robots_path.exists():
            print(f"[PyNext] No robots.txt found at {robots_path}")
            print("  Run: pynext robots generate")
            return 1
        
        content = robots_path.read_text()
        
        # Basic validation
        lines = content.strip().split("\n")
        has_user_agent = any(line.lower().startswith("user-agent:") for line in lines)
        has_sitemap = any(line.lower().startswith("sitemap:") for line in lines)
        
        print(f"[PyNext] Robots.txt Validation:\n")
        print(f"  ✓ File exists")
        print(f"  {'✓' if has_user_agent else '⚠'} Has User-agent directive")
        print(f"  {'✓' if has_sitemap else 'ℹ'} Has Sitemap directive")
        print(f"  Lines: {len(lines)}")
        
        return 0
    
    else:
        # No subcommand - show help
        print("\n[PyNext] Robots.txt Commands:\n")
        print("  pynext robots generate     Generate robots.txt")
        print("  pynext robots preview      Preview without generating")
        print("  pynext robots validate     Validate existing file")
        print()
        print("  Configure in pynext.config.py:")
        print()
        print("    from pynext import RobotsConfig, RobotsRule")
        print()
        print("    robots = RobotsConfig(")
        print("        rules=[")
        print('            RobotsRule(user_agent="*", allow=["/"], disallow=["/admin"]),')
        print("        ],")
        print("        sitemap=True,")
        print("    )")
        print()
        return 0


# ========================================
# cmd_og - OG Image commands
# ========================================

def cmd_og(args: argparse.Namespace) -> int:
    """Handle OG image subcommands."""
    from pathlib import Path
    
    root = Path(args.dir).resolve() if hasattr(args, "dir") else Path.cwd()
    
    if args.og_command == "preview":
        # Preview OG image for a route
        route_path = getattr(args, "route", "/")
        output = getattr(args, "output", None)
        
        print(f"\n[PyNext] Generating OG preview for: {route_path}\n")
        
        # Try to find the page and its OG config
        pages_dir = root / "pages"
        if not pages_dir.exists():
            pages_dir = root / "src" / "pages"
        
        if not pages_dir.exists():
            print("[PyNext] No pages directory found.")
            return 1
        
        # For preview, create a sample OG image
        try:
            from pynext.og import OGCanvas, OGRenderer
            from pynext.og.templates import minimal
            
            # Create sample canvas
            canvas = minimal.render({
                "title": f"Preview: {route_path}",
            })
            
            # Render
            renderer = OGRenderer()
            image_bytes = renderer.render(canvas)
            
            if output:
                output_path = Path(output)
                output_path.write_bytes(image_bytes)
                print(f"[PyNext] ✓ Saved preview to {output_path}")
            else:
                # Save to temp location
                output_path = root / ".pynext" / "og-preview.png"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(image_bytes)
                print(f"[PyNext] ✓ Saved preview to {output_path}")
            
            return 0
            
        except ImportError:
            print("[PyNext] Pillow is required for OG image generation.")
            print("  Install with: pip install Pillow")
            return 1
    
    elif args.og_command == "generate":
        # Generate all OG images
        output_dir = Path(getattr(args, "output_dir", root / "public" / "og"))
        
        print(f"\n[PyNext] Generating OG images to: {output_dir}\n")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Scan for pages with @og_image decorator
        from pynext.router.file_router import FileRouter
        
        pages_dir = root / "pages"
        if not pages_dir.exists():
            pages_dir = root / "src" / "pages"
        
        if not pages_dir.exists():
            print("[PyNext] No pages directory found.")
            return 1
        
        router = FileRouter(str(pages_dir))
        router.scan()
        
        generated = 0
        for route in router.routes:
            if hasattr(route.handler, "_og_config"):
                try:
                    from pynext.og import OGRenderer
                    from pynext.og.decorator import get_og_handler, get_og_config
                    
                    config = get_og_config(route.handler)
                    handler = get_og_handler(route.handler)
                    
                    # Generate canvas
                    if handler:
                        canvas = handler()
                    else:
                        canvas = config.template.render({"title": route.pattern.path})
                    
                    # Render
                    renderer = OGRenderer()
                    image_bytes = renderer.render(canvas, config.format)
                    
                    # Save
                    path_name = route.pattern.path.strip("/").replace("/", "-") or "index"
                    output_path = output_dir / f"{path_name}.{config.format}"
                    output_path.write_bytes(image_bytes)
                    
                    print(f"  ✓ {output_path.name}")
                    generated += 1
                    
                except Exception as e:
                    print(f"  ✗ {route.pattern.path}: {e}")
        
        print(f"\n[PyNext] Generated {generated} OG images\n")
        return 0
    
    elif args.og_command == "validate":
        # Validate OG configuration
        print("\n[PyNext] Validating OG configuration...\n")
        
        from pynext.router.file_router import FileRouter
        
        pages_dir = root / "pages"
        if not pages_dir.exists():
            pages_dir = root / "src" / "pages"
        
        if not pages_dir.exists():
            print("[PyNext] No pages directory found.")
            return 1
        
        router = FileRouter(str(pages_dir))
        router.scan()
        
        og_pages = []
        for route in router.routes:
            if hasattr(route.handler, "_og_config"):
                og_pages.append(route.pattern.path)
        
        if og_pages:
            print(f"  ✓ Found {len(og_pages)} pages with @og_image:\n")
            for path in og_pages:
                print(f"    - {path}")
        else:
            print("  ⚠ No pages with @og_image decorator found.")
        
        print()
        return 0
    
    else:
        # No subcommand - show help
        print("\n[PyNext] OG Image Commands:\n")
        print("  pynext og preview [route]    Preview OG image for a route")
        print("  pynext og generate           Generate all OG images")
        print("  pynext og validate           Validate OG configuration")
        print()
        print("  Example:")
        print("    pynext og preview /blog/my-post --output preview.png")
        print("    pynext og generate --output-dir public/og")
        print()
        return 0


# ========================================
# cmd_icons - Icon detection
# ========================================

def cmd_icons(args: argparse.Namespace) -> int:
    """Handle icons subcommands."""
    from pathlib import Path
    from pynext.pwa.icons import IconDetector
    
    root = Path(args.dir).resolve() if hasattr(args, "dir") else Path.cwd()
    public_dir = root / "public"
    
    if args.icons_command == "detect":
        if not public_dir.exists():
            print(f"[PyNext] No public/ directory found at {public_dir}")
            return 1
        
        detector = IconDetector(public_dir)
        icons = detector.detect()
        
        print("\n[PyNext] Detected Icons:\n")
        
        if icons.favicon:
            print(f"  ✓ Favicon: {icons.favicon}")
        else:
            print("  ✗ Favicon: Not found")
        
        if icons.icons:
            print(f"  ✓ App Icons: {len(icons.icons)}")
            for icon in icons.icons:
                size_str = f"{icon.size}x{icon.size}" if icon.size else "any"
                print(f"      - {icon.path} ({size_str})")
        else:
            print("  ✗ App Icons: Not found")
        
        if icons.apple_icon:
            print(f"  ✓ Apple Icon: {icons.apple_icon}")
        else:
            print("  ✗ Apple Icon: Not found")
        
        if icons.og_image:
            print(f"  ✓ OG Image: {icons.og_image}")
        else:
            print("  ✗ OG Image: Not found")
        
        # Show missing icons
        missing = detector.get_missing_icons()
        if missing:
            print("\n  ⚠ Missing (recommended):")
            for m in missing:
                print(f"    - {m}")
        
        print()
        return 0
    
    elif args.icons_command == "validate":
        if not public_dir.exists():
            print(f"[PyNext] No public/ directory found")
            return 1
        
        detector = IconDetector(public_dir)
        warnings = detector.validate()
        
        if not warnings:
            print("[PyNext] ✓ All icon requirements met")
            return 0
        
        print("[PyNext] ⚠ Icon validation warnings:\n")
        for w in warnings:
            print(f"  - {w}")
        print()
        return 0
    
    else:
        # No subcommand - show help
        print("\n[PyNext] Icon Commands:\n")
        print("  pynext icons detect      Detect icons from public/")
        print("  pynext icons validate    Validate PWA icon requirements")
        print()
        return 0


# ========================================
# cmd_manifest - PWA manifest
# ========================================

def cmd_manifest(args: argparse.Namespace) -> int:
    """Handle manifest subcommands."""
    from pathlib import Path
    from pynext.pwa.icons import IconDetector
    from pynext.pwa.manifest import PWAManifest, ManifestGenerator
    
    root = Path(args.dir).resolve() if hasattr(args, "dir") else Path.cwd()
    public_dir = root / "public"
    
    def load_manifest_config() -> PWAManifest:
        """Load manifest config from pynext.config.py or default."""
        config_path = root / "pynext.config.py"
        
        if config_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("pynext_config", config_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "manifest"):
                    return module.manifest
        
        # Default manifest
        return PWAManifest(name="PyNext App")
    
    if args.manifest_command == "generate":
        config = load_manifest_config()
        
        # Detect icons if available
        icons = None
        if public_dir.exists():
            detector = IconDetector(public_dir)
            icons = detector.detect()
        
        # Generate manifest
        if icons:
            from pynext.pwa.manifest import ManifestGenerator
            generator = ManifestGenerator(config, icons)
            content = generator.generate()
        else:
            content = config.to_json()
        
        # Write to file
        output_path = Path(getattr(args, "output", None) or public_dir / "manifest.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        
        print(f"[PyNext] ✓ Generated manifest.json")
        print(f"  → {output_path.relative_to(root)}")
        return 0
    
    elif args.manifest_command == "preview":
        config = load_manifest_config()
        
        # Detect icons
        icons = None
        if public_dir.exists():
            detector = IconDetector(public_dir)
            icons = detector.detect()
        
        # Generate and display
        if icons and not config.icons:
            from pynext.pwa.manifest import ManifestGenerator
            generator = ManifestGenerator(config, icons)
            content = generator.generate()
        else:
            content = config.to_json()
        
        print("[PyNext] Manifest Preview:\n")
        print(content)
        print()
        return 0
    
    else:
        # No subcommand - show help
        print("\n[PyNext] Manifest Commands:\n")
        print("  pynext manifest generate   Generate manifest.json")
        print("  pynext manifest preview    Preview without generating")
        print()
        print("  Configure in pynext.config.py:")
        print()
        print("    from pynext import PWAManifest")
        print()
        print("    manifest = PWAManifest(")
        print('        name="My App",')
        print('        theme_color="#3b82f6",')
        print("    )")
        print()
        return 0


# ========================================
# cmd_pwa - PWA validation
# ========================================

def cmd_lint(args: argparse.Namespace) -> int:
    """Run PyNext linting."""
    from pathlib import Path
    from pynext.lint import lint, fix, LintResult
    from pynext.lint.config import (
        create_config_file, create_vscode_config, load_config
    )
    from pynext.lint.rules import explain_rule, get_all_rules
    from pynext.lint.lsp import start_lsp_server
    from pynext.lint.runner import format_errors
    
    project_dir = Path(args.dir).resolve()
    
    # Handle subcommands
    lint_cmd = getattr(args, "lint_command", None)
    
    if lint_cmd == "init":
        # Create config file
        format_type = "ruff" if getattr(args, "ruff", False) else "pyproject"
        config_path = create_config_file(project_dir, format_type)
        print(f"[PyNext] Created config: {config_path}")
        return 0
    
    elif lint_cmd == "vscode":
        # Create VS Code config
        settings_path = create_vscode_config(project_dir)
        print(f"[PyNext] Created VS Code config: {settings_path}")
        print("[PyNext] Recommended extensions:")
        print("  - charliermarsh.ruff")
        print("  - ms-python.python")
        return 0
    
    elif lint_cmd == "rules":
        # List all rules
        print("\n[PyNext] Linting Rules:\n")
        rules = get_all_rules()
        for rule_id, info in sorted(rules.items()):
            auto_fix = "✓" if info["auto_fix"] else " "
            severity = info["severity"][:3].upper()
            print(f"  {rule_id} [{severity}] [{auto_fix}] {info['name']}")
            print(f"        {info['description']}")
        print()
        print("  Legend: [ERR]=error [WAR]=warning [INF]=info [✓]=auto-fixable")
        return 0
    
    elif lint_cmd == "explain":
        # Explain a rule
        rule_id = getattr(args, "rule", "")
        if not rule_id:
            print("[PyNext] Error: Please specify a rule (e.g., pynext lint explain PNX001)")
            return 1
        
        explanation = explain_rule(rule_id.upper())
        print(explanation)
        return 0
    
    elif lint_cmd == "lsp":
        # Start LSP server
        print("[PyNext] Starting LSP server...", file=__import__("sys").stderr)
        start_lsp_server()
        return 0
    
    else:
        # Default: run linting
        target = getattr(args, "target", ".")
        auto_fix = getattr(args, "fix", False)
        unsafe = getattr(args, "unsafe", False)
        output_format = getattr(args, "format", "text")
        
        # Run linting
        if auto_fix:
            print(f"[PyNext] Fixing issues in {target}...")
            result = fix(target, unsafe=unsafe)
        else:
            print(f"[PyNext] Linting {target}...")
            result = lint(target)
        
        # Output results
        output = format_errors(result, output_format)
        print(output)
        
        # Return exit code
        return 1 if result.has_errors else 0


def cmd_pwa(args: argparse.Namespace) -> int:
    """Handle pwa subcommands."""
    from pathlib import Path
    from pynext.pwa.icons import IconDetector
    
    root = Path(args.dir).resolve() if hasattr(args, "dir") else Path.cwd()
    public_dir = root / "public"
    
    if args.pwa_command == "validate":
        print("\n[PyNext] PWA Validation:\n")
        
        issues = []
        passed = []
        
        # Check for manifest
        manifest_path = public_dir / "manifest.json"
        config_path = root / "pynext.config.py"
        
        has_manifest = manifest_path.exists()
        has_config = False
        
        if config_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("pynext_config", config_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                has_config = hasattr(module, "manifest")
        
        if has_manifest or has_config:
            passed.append("Manifest: Found")
        else:
            issues.append("Manifest: Not found. Run 'pynext manifest generate' or add to pynext.config.py")
        
        # Check icons
        if public_dir.exists():
            detector = IconDetector(public_dir)
            icons = detector.detect()
            icon_warnings = detector.validate()
            
            if icons.favicon:
                passed.append(f"Favicon: {icons.favicon}")
            else:
                issues.append("Favicon: Not found")
            
            sizes = {i.size for i in icons.icons if i.size}
            if 192 in sizes:
                passed.append("Icon 192x192: Found")
            else:
                issues.append("Icon 192x192: Required for PWA")
            
            if 512 in sizes:
                passed.append("Icon 512x512: Found")
            else:
                issues.append("Icon 512x512: Required for splash screen")
        else:
            issues.append("public/ directory: Not found")
        
        # Print results
        for p in passed:
            print(f"  ✓ {p}")
        
        for i in issues:
            print(f"  ✗ {i}")
        
        print()
        
        if issues:
            print(f"  {len(issues)} issue(s) found")
            return 1
        else:
            print("  ✓ PWA requirements met!")
            return 0
    
    else:
        # No subcommand - show help
        print("\n[PyNext] PWA Commands:\n")
        print("  pynext pwa validate    Validate PWA requirements")
        print()
        print("  Related commands:")
        print("    pynext icons detect       Detect icons")
        print("    pynext manifest generate  Generate manifest.json")
        print()
        return 0


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pynext",
        description="PyNext - A Python web framework with SolidJS-inspired reactivity",
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # dev command
    dev_parser = subparsers.add_parser("dev", help="Start development server")
    dev_parser.add_argument("--pages", default="pages", help="Pages directory")
    dev_parser.add_argument("--static", default="public", help="Static files directory")
    dev_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    dev_parser.add_argument("--port", "-p", type=int, default=3000, help="Port to listen on")
    dev_parser.add_argument("--skip-deps", action="store_true", help="Skip dependency check")
    dev_parser.add_argument("--no-install", action="store_true", help="Don't auto-install missing deps")
    
    # build command
    build_parser = subparsers.add_parser("build", help="Build for production")
    build_parser.add_argument("--dir", default=".", help="Project directory")
    build_parser.add_argument("--pages", default="pages", help="Pages directory")
    build_parser.add_argument("--static", default="public", help="Static files directory")
    build_parser.add_argument("--output", "-o", default=".pynext/build", help="Output directory")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize new project")
    init_parser.add_argument("name", help="Project name/directory")
    init_parser.add_argument("--src", action="store_true", help="Use src/ directory structure")
    init_parser.add_argument("--yes", "-y", action="store_true", help="Skip prompts, use defaults")
    
    # routes command
    routes_parser = subparsers.add_parser("routes", help="List all routes")
    routes_parser.add_argument("--pages", default="pages", help="Pages directory")
    
    # ========================================
    # pynext generate / pynext g
    # ========================================
    gen_parser = subparsers.add_parser(
        "generate",
        aliases=["g"],
        help="Generate components, pages, APIs, etc."
    )
    gen_parser.add_argument(
        "type",
        choices=["page", "component", "api", "layout", "template", 
                 "loading", "error", "middleware", "island", "action", "hook"],
        help="Type of component to generate"
    )
    gen_parser.add_argument("name", help="Component name (can include path: blog/posts)")
    gen_parser.add_argument(
        "--minimal",
        dest="template_style",
        action="store_const",
        const="minimal",
        default="full",
        help="Use minimal template (less boilerplate)"
    )
    gen_parser.add_argument(
        "--full",
        dest="template_style",
        action="store_const",
        const="full",
        help="Use full template with examples (default)"
    )
    gen_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip interactive prompts"
    )
    gen_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing files"
    )
    gen_parser.add_argument(
        "--ai",
        action="store_true",
        help="Use AI-assisted generation (requires ANTHROPIC_API_KEY)"
    )
    gen_parser.add_argument(
        "--prompt", "-p",
        help="Direct prompt for AI generation (skips interview)"
    )
    gen_parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )
    
    # deps command
    deps_parser = subparsers.add_parser("deps", help="Manage dependencies")
    deps_subparsers = deps_parser.add_subparsers(dest="deps_command", help="Dependency commands")
    
    # deps install
    deps_install = deps_subparsers.add_parser("install", help="Install dependencies")
    deps_install.add_argument("--dir", default=".", help="Project directory")
    deps_install.add_argument("--python", dest="python_only", action="store_true", help="Install only Python deps")
    deps_install.add_argument("--npm", dest="npm_only", action="store_true", help="Install only NPM deps")
    
    # deps check
    deps_check = deps_subparsers.add_parser("check", help="Check for missing dependencies")
    deps_check.add_argument("--dir", default=".", help="Project directory")
    
    # deps init
    deps_init = deps_subparsers.add_parser("init", help="Create dependency files")
    deps_init.add_argument("--dir", default=".", help="Project directory")
    
    # ui command (Tier 2: Official components)
    ui_parser = subparsers.add_parser("ui", help="Manage UI components")
    ui_parser.add_argument("--dir", default=".", help="Project directory")
    ui_subparsers = ui_parser.add_subparsers(dest="ui_command", help="UI commands")
    
    # ui add
    ui_add = ui_subparsers.add_parser("add", help="Add UI components to project")
    ui_add.add_argument("components", nargs="*", help="Component names to add")
    ui_add.add_argument("--all", action="store_true", help="Add all components")
    
    # ui list
    ui_subparsers.add_parser("list", help="List available components")
    
    # registry command (Tier 3: Custom registries)
    reg_parser = subparsers.add_parser("registry", help="Manage custom component registries")
    reg_parser.add_argument("--dir", default=".", help="Project directory")
    reg_subparsers = reg_parser.add_subparsers(dest="registry_command", help="Registry commands")
    
    # registry add
    reg_add = reg_subparsers.add_parser("add", help="Add a custom registry")
    reg_add.add_argument("name", help="Registry name")
    reg_add.add_argument("--url", help="Registry URL (https:// or github:owner/repo)")
    
    # registry remove
    reg_remove = reg_subparsers.add_parser("remove", help="Remove a registry")
    reg_remove.add_argument("name", help="Registry name to remove")
    
    # registry list
    reg_subparsers.add_parser("list", help="List registered sources")
    
    # registry install
    reg_install = reg_subparsers.add_parser("install", help="Install from registry")
    reg_install.add_argument("component", help="Component to install (registry:component)")
    
    # registry init
    reg_subparsers.add_parser("init", help="Create registry template for publishing")
    
    # ========================================
    # pynext og
    # ========================================
    og_parser = subparsers.add_parser("og", help="OG image generation")
    og_parser.add_argument("--dir", default=".", help="Project directory")
    og_subparsers = og_parser.add_subparsers(dest="og_command", help="OG commands")
    
    # og preview
    og_preview = og_subparsers.add_parser("preview", help="Preview OG image for a route")
    og_preview.add_argument("route", nargs="?", default="/", help="Route path to preview")
    og_preview.add_argument("--output", "-o", help="Output file path")
    
    # og generate
    og_generate = og_subparsers.add_parser("generate", help="Generate all OG images")
    og_generate.add_argument("--output-dir", help="Output directory for OG images")
    
    # og validate
    og_subparsers.add_parser("validate", help="Validate OG configuration")
    
    # ========================================
    # pynext icons
    # ========================================
    icons_parser = subparsers.add_parser("icons", help="Icon detection and validation")
    icons_parser.add_argument("--dir", default=".", help="Project directory")
    icons_subparsers = icons_parser.add_subparsers(dest="icons_command", help="Icon commands")
    
    # icons detect
    icons_subparsers.add_parser("detect", help="Detect icons from public/")
    
    # icons validate
    icons_subparsers.add_parser("validate", help="Validate PWA icon requirements")
    
    # ========================================
    # pynext manifest
    # ========================================
    manifest_parser = subparsers.add_parser("manifest", help="PWA manifest generation")
    manifest_parser.add_argument("--dir", default=".", help="Project directory")
    manifest_subparsers = manifest_parser.add_subparsers(dest="manifest_command", help="Manifest commands")
    
    # manifest generate
    manifest_gen = manifest_subparsers.add_parser("generate", help="Generate manifest.json")
    manifest_gen.add_argument("--output", "-o", help="Output file path")
    
    # manifest preview
    manifest_subparsers.add_parser("preview", help="Preview without generating")
    
    # ========================================
    # pynext pwa
    # ========================================
    pwa_parser = subparsers.add_parser("pwa", help="PWA validation")
    pwa_parser.add_argument("--dir", default=".", help="Project directory")
    pwa_subparsers = pwa_parser.add_subparsers(dest="pwa_command", help="PWA commands")
    
    # pwa validate
    pwa_subparsers.add_parser("validate", help="Validate PWA requirements")
    
    # ========================================
    # pynext sitemap
    # ========================================
    sitemap_parser = subparsers.add_parser("sitemap", help="Sitemap generation")
    sitemap_parser.add_argument("--dir", default=".", help="Project directory")
    sitemap_parser.add_argument("--base-url", help="Base URL (e.g., https://example.com)")
    sitemap_subparsers = sitemap_parser.add_subparsers(dest="sitemap_command", help="Sitemap commands")
    
    # sitemap generate
    sitemap_gen = sitemap_subparsers.add_parser("generate", help="Generate sitemap.xml")
    sitemap_gen.add_argument("--output", "-o", help="Output directory (default: public/)")
    
    # sitemap validate
    sitemap_subparsers.add_parser("validate", help="Validate existing sitemap")
    
    # sitemap preview
    sitemap_preview = sitemap_subparsers.add_parser("preview", help="Preview URLs without generating")
    sitemap_preview.add_argument("--limit", "-n", type=int, default=20, help="Number of URLs to show")
    
    # ========================================
    # pynext robots
    # ========================================
    robots_parser = subparsers.add_parser("robots", help="Robots.txt management")
    robots_parser.add_argument("--dir", default=".", help="Project directory")
    robots_parser.add_argument("--base-url", help="Base URL for sitemap reference")
    robots_subparsers = robots_parser.add_subparsers(dest="robots_command", help="Robots commands")
    
    # robots generate
    robots_gen = robots_subparsers.add_parser("generate", help="Generate robots.txt")
    robots_gen.add_argument("--output", "-o", help="Output file path")
    
    # robots preview
    robots_subparsers.add_parser("preview", help="Preview without generating")
    
    # robots validate
    robots_subparsers.add_parser("validate", help="Validate existing file")
    
    # ========================================
    # pynext lint
    # ========================================
    lint_parser = subparsers.add_parser("lint", help="Lint your PyNext project")
    lint_parser.add_argument("target", nargs="?", default=".", help="File or directory to lint")
    lint_parser.add_argument("--dir", default=".", help="Project directory")
    lint_parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    lint_parser.add_argument("--unsafe", action="store_true", help="Include unsafe fixes")
    lint_parser.add_argument("--format", "-f", choices=["text", "json", "github"], 
                            default="text", help="Output format")
    lint_subparsers = lint_parser.add_subparsers(dest="lint_command", help="Lint commands")
    
    # lint init
    lint_init = lint_subparsers.add_parser("init", help="Create lint configuration file")
    lint_init.add_argument("--ruff", action="store_true", help="Create .ruff.toml instead of pyproject.toml")
    
    # lint vscode
    lint_subparsers.add_parser("vscode", help="Configure VS Code for linting")
    
    # lint rules
    lint_subparsers.add_parser("rules", help="List all PyNext-specific rules")
    
    # lint explain
    lint_explain = lint_subparsers.add_parser("explain", help="Explain a rule in detail")
    lint_explain.add_argument("rule", help="Rule ID (e.g., PNX001)")
    
    # lint lsp
    lint_subparsers.add_parser("lsp", help="Start LSP server for editor integration")
    
    # ========================================
    # pynext env
    # ========================================
    env_parser = subparsers.add_parser("env", help="Environment variable management")
    env_parser.add_argument("--dir", default=".", help="Project directory")
    env_subparsers = env_parser.add_subparsers(dest="env_command", help="Environment commands")
    
    # env list
    env_list = env_subparsers.add_parser("list", help="List all environment variables")
    env_list.add_argument("--show-values", "-v", action="store_true", help="Show values (secrets masked)")
    env_list.add_argument("--public", "-p", action="store_true", help="Show only PYNEXT_PUBLIC_* vars")
    env_list.add_argument("--mode", "-m", default="development", help="Mode (development/production/test)")
    
    # env check
    env_check = env_subparsers.add_parser("check", help="Check which env files exist")
    env_check.add_argument("--mode", "-m", default="development", help="Mode to check")
    
    # env validate
    env_validate = env_subparsers.add_parser("validate", help="Validate env against schema")
    env_validate.add_argument("--mode", "-m", default="production", help="Mode to validate")
    
    # env init
    env_init = env_subparsers.add_parser("init", help="Create .env from schema template")
    env_init.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")
    
    # env generate
    env_generate = env_subparsers.add_parser("generate", help="Generate TypeScript types")
    env_generate.add_argument("--output", "-o", help="Output file path (default: env.d.ts)")
    
    args = parser.parse_args()
    
    if args.version:
        from pynext import __version__
        print(f"pynext {__version__}")
        return 0
    
    if args.command == "dev":
        return cmd_dev(args)
    elif args.command == "build":
        return cmd_build(args)
    elif args.command == "init":
        return cmd_init(args)
    elif args.command == "routes":
        return cmd_routes(args)
    elif args.command in ("generate", "g"):
        return cmd_generate(args)
    elif args.command == "deps":
        return cmd_deps(args)
    elif args.command == "ui":
        return cmd_ui(args)
    elif args.command == "registry":
        return cmd_registry(args)
    elif args.command == "env":
        return cmd_env(args)
    elif args.command == "lint":
        return cmd_lint(args)
    elif args.command == "sitemap":
        return cmd_sitemap(args)
    elif args.command == "robots":
        return cmd_robots(args)
    elif args.command == "og":
        return cmd_og(args)
    elif args.command == "icons":
        return cmd_icons(args)
    elif args.command == "manifest":
        return cmd_manifest(args)
    elif args.command == "pwa":
        return cmd_pwa(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

