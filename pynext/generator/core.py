"""
Component generator core.

Simple, predictable file generation.
Detects project structure and creates files in the right place.

Example:
    gen = Generator(project_root)
    gen.create("page", "blog")           # Creates pages/blog.py
    gen.create("component", "Button")    # Creates components/Button.py
    gen.create("island", "Counter")      # Creates components/Counter.py with @island

Why This Design:
    - Single Generator class handles all types
    - Auto-detects src/ folder structure
    - Templates are separate for easy customization
    - Validation catches errors early
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Literal, Optional

from pynext.generator.templates import get_template, render_template
from pynext.generator.validators import (
    validate_name,
    validate_path,
    to_title_case,
    get_route_path,
    ValidationError,
)


# ============================================
# Configuration
# ============================================

@dataclass
class GeneratorConfig:
    """
    Configuration for a single generation.
    
    Attributes:
        name: Component name
        generator_type: Type (page, component, api, etc.)
        template_style: "minimal" or "full"
        output_dir: Override output location
        props: Additional template variables
    
    Example:
        config = GeneratorConfig(
            name="ProductCard",
            generator_type="component",
            template_style="full",
            props={"has_image": True},
        )
    """
    name: str
    generator_type: str
    template_style: Literal["minimal", "full"] = "full"
    output_dir: Optional[Path] = None
    props: Dict = field(default_factory=dict)


# Directory mappings for each generator type
OUTPUT_DIRS = {
    "page": "pages",
    "component": "components",
    "island": "components",
    "api": "pages/api",
    "layout": "pages",
    "template": "pages",
    "loading": "pages",
    "error": "pages",
    "middleware": "",  # Root directory
    "action": "actions",
    "hook": "hooks",
}

# File name patterns
FILE_NAMES = {
    "layout": "layout.py",
    "template": "template.py",
    "loading": "loading.py",
    "error": "error.py",
    "middleware": "middleware.py",
}


# ============================================
# Generator Class
# ============================================

class Generator:
    """
    Component generator.
    
    Creates pages, components, APIs, and more with sensible defaults.
    Auto-detects project structure (src/ folder support).
    
    Attributes:
        root: Project root directory
        use_src: Whether project uses src/ folder
        base: Base directory for files (root or root/src)
    
    Example:
        gen = Generator(Path("."))
        
        # Create a page
        gen.create("page", "blog")
        
        # Create a component with full template
        gen.create("component", "UserCard", template_style="full")
        
        # Create from AI-generated content
        gen.create_from_content("page", "products", ai_generated_code)
    """
    
    def __init__(self, root: Path):
        """
        Initialize generator.
        
        Args:
            root: Project root directory
        
        Example:
            gen = Generator(Path("."))
            gen = Generator(Path("/my/project"))
        """
        self.root = Path(root).resolve()
        self._detect_src_folder()
    
    def _detect_src_folder(self):
        """
        Auto-detect src/ folder structure.
        
        If pages/ exists in src/, use src/ as base.
        Otherwise, use project root as base.
        """
        src_pages = self.root / "src" / "pages"
        root_pages = self.root / "pages"
        
        if src_pages.exists():
            self.use_src = True
            self.base = self.root / "src"
        elif root_pages.exists():
            self.use_src = False
            self.base = self.root
        else:
            # No pages dir yet - default to root
            self.use_src = False
            self.base = self.root
    
    def _get_output_path(self, generator_type: str, name: str) -> Path:
        """
        Get output file path for a generator.
        
        Args:
            generator_type: Type of generator
            name: Component name (can include path segments)
        
        Returns:
            Absolute path where file should be created
        """
        # Get base directory for this type
        type_dir = OUTPUT_DIRS.get(generator_type, "")
        
        # Handle path-based names (e.g., "blog/posts" for nested pages)
        if "/" in name:
            path_parts = name.rsplit("/", 1)
            dir_path = path_parts[0]
            file_name = path_parts[1]
        else:
            dir_path = ""
            file_name = name
        
        # Get file name (some types have fixed names)
        if generator_type in FILE_NAMES:
            # For layout, template, etc. - the name is the directory
            if dir_path:
                full_dir = dir_path
            else:
                full_dir = file_name
            final_name = FILE_NAMES[generator_type]
            
            return self.base / type_dir / full_dir / final_name
        else:
            # For pages, components - name is the file
            if dir_path:
                return self.base / type_dir / dir_path / f"{file_name}.py"
            else:
                return self.base / type_dir / f"{file_name}.py"
    
    def create(
        self,
        generator_type: str,
        name: str,
        template_style: str = "full",
        props: Optional[Dict] = None,
        force: bool = False,
    ) -> Path:
        """
        Create a new component.
        
        Args:
            generator_type: Type (page, component, api, layout, etc.)
            name: Component name
            template_style: "minimal" or "full"
            props: Additional template variables
            force: Overwrite if exists
        
        Returns:
            Path to created file
        
        Raises:
            ValidationError: If name is invalid
            FileExistsError: If file exists and force=False
        
        Example:
            # Basic page
            gen.create("page", "blog")
            
            # Component with props
            gen.create("component", "Card", props={"has_image": True})
            
            # Nested page
            gen.create("page", "products/[id]")
            
            # Force overwrite
            gen.create("page", "blog", force=True)
        """
        # For nested paths, validate only the final component name
        if "/" in name:
            final_name = name.rsplit("/", 1)[-1]
        else:
            final_name = name
        
        # Validate name (just the final part for nested paths)
        validated_name = validate_name(final_name, generator_type)
        
        # Get output path
        output_path = self._get_output_path(generator_type, name)
        
        # Check if exists
        if output_path.exists() and not force:
            raise FileExistsError(
                f"File already exists: {output_path}\n"
                f"Use --force to overwrite."
            )
        
        # Get template
        template = get_template(generator_type, template_style)
        
        # Build template context
        context = {
            "name": validated_name,
            "title": to_title_case(name.split("/")[-1]),
            "route": get_route_path(name),
            **(props or {}),
        }
        
        # Render template
        content = render_template(template, **context)
        
        # Create directories
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        output_path.write_text(content)
        
        return output_path
    
    def create_from_content(
        self,
        generator_type: str,
        name: str,
        content: str,
        force: bool = False,
    ) -> Path:
        """
        Create a component from provided content.
        
        Used for AI-generated code.
        
        Args:
            generator_type: Type of generator
            name: Component name
            content: Python code content
            force: Overwrite if exists
        
        Returns:
            Path to created file
        
        Example:
            ai_code = generate_with_ai("page", "products", answers)
            gen.create_from_content("page", "products", ai_code)
        """
        # Validate name
        validate_name(name, generator_type)
        
        # Get output path
        output_path = self._get_output_path(generator_type, name)
        
        # Check if exists
        if output_path.exists() and not force:
            raise FileExistsError(
                f"File already exists: {output_path}\n"
                f"Use --force to overwrite."
            )
        
        # Create directories
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        output_path.write_text(content)
        
        return output_path
    
    def list_existing(self, generator_type: str) -> list[Path]:
        """
        List existing files of a given type.
        
        Args:
            generator_type: Type to list
        
        Returns:
            List of existing file paths
        
        Example:
            pages = gen.list_existing("page")
            components = gen.list_existing("component")
        """
        type_dir = OUTPUT_DIRS.get(generator_type, "")
        search_dir = self.base / type_dir
        
        if not search_dir.exists():
            return []
        
        return list(search_dir.rglob("*.py"))
    
    def get_output_path_preview(self, generator_type: str, name: str) -> Path:
        """
        Preview where a file would be created.
        
        Args:
            generator_type: Type of generator
            name: Component name
        
        Returns:
            Path where file would be created (relative to project root)
        
        Example:
            path = gen.get_output_path_preview("page", "blog")
            print(f"Would create: {path}")
        """
        output_path = self._get_output_path(generator_type, name)
        try:
            return output_path.relative_to(self.root)
        except ValueError:
            return output_path


# ============================================
# Convenience Functions
# ============================================

def create_component(
    name: str,
    generator_type: str = "component",
    template_style: str = "full",
    root: Optional[Path] = None,
) -> Path:
    """
    Convenience function to create a component.
    
    Args:
        name: Component name
        generator_type: Type of generator
        template_style: "minimal" or "full"
        root: Project root (defaults to cwd)
    
    Returns:
        Path to created file
    
    Example:
        create_component("Button")
        create_component("blog", generator_type="page")
    """
    gen = Generator(root or Path.cwd())
    return gen.create(generator_type, name, template_style)

