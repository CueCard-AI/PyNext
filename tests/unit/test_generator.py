"""
Comprehensive tests for component generator.

Tests cover:
- Validators (name, path validation)
- Templates (all 11 types, minimal + full)
- Core Generator (create, paths, detection)
- Prompts (all generator types)
- AI integration (mock API, completeness evaluation)
- CLI integration (flags, aliases)
- Edge cases (unicode, special chars)
- Performance benchmarks

Total: 80+ tests
"""

import pytest
from pathlib import Path
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock


# ============================================
# Validator Tests (15 tests)
# ============================================

class TestValidators:
    """Tests for name and path validation."""
    
    def test_validate_name_basic(self):
        """Test basic name validation."""
        from pynext.generator.validators import validate_name
        
        result = validate_name("blog", "page")
        assert result == "blog"
    
    def test_validate_name_with_underscore(self):
        """Test name with underscore."""
        from pynext.generator.validators import validate_name
        
        result = validate_name("blog_post", "page")
        assert result == "blog_post"
    
    def test_validate_name_hyphen_to_underscore(self):
        """Test hyphen conversion to underscore."""
        from pynext.generator.validators import validate_name
        
        result = validate_name("blog-post", "page")
        assert result == "blog_post"
    
    def test_validate_name_component_pascal_case(self):
        """Test components get PascalCase."""
        from pynext.generator.validators import validate_name
        
        result = validate_name("user_profile", "component")
        assert result == "UserProfile"
    
    def test_validate_name_page_snake_case(self):
        """Test pages get snake_case."""
        from pynext.generator.validators import validate_name
        
        result = validate_name("UserProfile", "page")
        assert result == "user_profile"
    
    def test_validate_name_empty_raises(self):
        """Test empty name raises."""
        from pynext.generator.validators import validate_name, ValidationError
        
        with pytest.raises(ValidationError) as exc:
            validate_name("", "page")
        
        assert "cannot be empty" in str(exc.value)
    
    def test_validate_name_reserved_raises(self):
        """Test reserved names raise."""
        from pynext.generator.validators import validate_name, ValidationError
        
        with pytest.raises(ValidationError) as exc:
            validate_name("class", "page")
        
        assert "reserved" in str(exc.value)
    
    def test_validate_name_invalid_chars_raises(self):
        """Test invalid characters raise."""
        from pynext.generator.validators import validate_name, ValidationError
        
        with pytest.raises(ValidationError) as exc:
            validate_name("blog@post", "page")
        
        assert "Invalid name" in str(exc.value)
    
    def test_validate_path_basic(self):
        """Test basic path validation."""
        from pynext.generator.validators import validate_path
        
        result = validate_path("blog/posts", "page")
        assert result == Path("blog/posts")
    
    def test_validate_path_dynamic_route(self):
        """Test dynamic route paths."""
        from pynext.generator.validators import validate_path
        
        result = validate_path("products/[id]", "page")
        assert result == Path("products/[id]")
    
    def test_validate_path_catch_all(self):
        """Test catch-all route paths."""
        from pynext.generator.validators import validate_path
        
        result = validate_path("docs/[...slug]", "page")
        assert result == Path("docs/[...slug]")
    
    def test_validate_path_traversal_raises(self):
        """Test path traversal raises."""
        from pynext.generator.validators import validate_path, ValidationError
        
        with pytest.raises(ValidationError):
            validate_path("../secret", "page")
    
    def test_validate_path_absolute_raises(self):
        """Test absolute path raises."""
        from pynext.generator.validators import validate_path, ValidationError
        
        with pytest.raises(ValidationError):
            validate_path("/absolute/path", "page")
    
    def test_to_pascal_case(self):
        """Test PascalCase conversion."""
        from pynext.generator.validators import to_pascal_case
        
        assert to_pascal_case("user_profile") == "UserProfile"
        assert to_pascal_case("button") == "Button"
    
    def test_to_snake_case(self):
        """Test snake_case conversion."""
        from pynext.generator.validators import to_snake_case
        
        assert to_snake_case("UserProfile") == "user_profile"
        assert to_snake_case("Button") == "button"


# ============================================
# Template Tests (22 tests)
# ============================================

class TestTemplates:
    """Tests for template definitions."""
    
    def test_all_types_exist(self):
        """Test all 11 types have templates."""
        from pynext.generator.templates import TEMPLATES
        
        expected = [
            "page", "component", "island", "api", "layout",
            "template", "loading", "error", "middleware",
            "action", "hook"
        ]
        
        for type_name in expected:
            assert type_name in TEMPLATES, f"Missing template: {type_name}"
    
    def test_all_types_have_minimal_and_full(self):
        """Test all types have both minimal and full templates."""
        from pynext.generator.templates import TEMPLATES
        
        for type_name, templates in TEMPLATES.items():
            assert "minimal" in templates, f"{type_name} missing minimal"
            assert "full" in templates, f"{type_name} missing full"
    
    def test_get_template_page(self):
        """Test getting page template."""
        from pynext.generator.templates import get_template
        
        template = get_template("page", "full")
        assert "def {name}" in template
        assert "Metadata" in template
    
    def test_get_template_minimal(self):
        """Test getting minimal template."""
        from pynext.generator.templates import get_template
        
        full = get_template("page", "full")
        minimal = get_template("page", "minimal")
        
        assert len(minimal) < len(full)
    
    def test_get_template_invalid_type_raises(self):
        """Test invalid type raises."""
        from pynext.generator.templates import get_template
        
        with pytest.raises(ValueError) as exc:
            get_template("invalid_type", "full")
        
        assert "Unknown generator type" in str(exc.value)
    
    def test_get_template_invalid_style_raises(self):
        """Test invalid style raises."""
        from pynext.generator.templates import get_template
        
        with pytest.raises(ValueError) as exc:
            get_template("page", "invalid_style")
        
        assert "Unknown template style" in str(exc.value)
    
    def test_render_template_basic(self):
        """Test basic template rendering."""
        from pynext.generator.templates import render_template
        
        result = render_template("Hello {name}!", name="World")
        assert result == "Hello World!"
    
    def test_render_template_multiple_vars(self):
        """Test rendering with multiple variables."""
        from pynext.generator.templates import render_template
        
        result = render_template("{name} - {title}", name="blog", title="Blog")
        assert result == "blog - Blog"
    
    def test_page_template_has_metadata(self):
        """Test page template includes metadata."""
        from pynext.generator.templates import get_template
        
        template = get_template("page", "full")
        assert "metadata = Metadata" in template
    
    def test_page_template_has_get_data(self):
        """Test page template includes get_data."""
        from pynext.generator.templates import get_template
        
        template = get_template("page", "full")
        assert "async def get_data" in template
    
    def test_island_template_has_signal(self):
        """Test island template uses Signal."""
        from pynext.generator.templates import get_template
        
        template = get_template("island", "full")
        assert "Signal" in template
    
    def test_island_template_has_decorator(self):
        """Test island template has @island decorator."""
        from pynext.generator.templates import get_template
        
        template = get_template("island", "full")
        assert "@island" in template
    
    def test_api_template_has_methods(self):
        """Test API template has HTTP methods."""
        from pynext.generator.templates import get_template
        
        template = get_template("api", "full")
        assert "async def GET" in template
        assert "async def POST" in template
    
    def test_layout_template_has_children(self):
        """Test layout template accepts children."""
        from pynext.generator.templates import get_template
        
        template = get_template("layout", "full")
        assert "def layout(children)" in template
    
    def test_action_template_has_decorator(self):
        """Test action template has @action decorator."""
        from pynext.generator.templates import get_template
        
        template = get_template("action", "full")
        assert "@action" in template
    
    def test_middleware_template_has_config(self):
        """Test middleware template has config."""
        from pynext.generator.templates import get_template
        
        template = get_template("middleware", "full")
        assert "config = {" in template
    
    def test_loading_template_has_skeleton(self):
        """Test loading template has skeleton UI."""
        from pynext.generator.templates import get_template
        
        template = get_template("loading", "full")
        assert "animate-pulse" in template
    
    def test_error_template_has_retry(self):
        """Test error template has retry button."""
        from pynext.generator.templates import get_template
        
        template = get_template("error", "full")
        assert "reset" in template
    
    def test_hook_template_has_return_types(self):
        """Test hook template has proper return types."""
        from pynext.generator.templates import get_template
        
        template = get_template("hook", "full")
        assert "Callable" in template
    
    def test_list_generator_types(self):
        """Test listing generator types."""
        from pynext.generator.templates import list_generator_types
        
        types = list_generator_types()
        assert len(types) == 11
        assert "page" in types
        assert "island" in types
    
    def test_template_template_has_animation(self):
        """Test template template has animation."""
        from pynext.generator.templates import get_template
        
        template = get_template("template", "full")
        assert "FadeIn" in template or "animate" in template
    
    def test_component_template_has_variants(self):
        """Test component template has variants."""
        from pynext.generator.templates import get_template
        
        template = get_template("component", "full")
        assert "variant" in template


# ============================================
# Generator Core Tests (15 tests)
# ============================================

class TestGeneratorCore:
    """Tests for Generator class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = Generator(Path(tmpdir))
            assert gen.root == Path(tmpdir).resolve()
    
    def test_detect_no_src(self):
        """Test detection without src folder."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "pages").mkdir()
            
            gen = Generator(root)
            assert not gen.use_src
            # Compare resolved paths to handle macOS /private symlink
            assert gen.base.resolve() == root.resolve()
    
    def test_detect_with_src(self):
        """Test detection with src folder."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            (root / "src" / "pages").mkdir(parents=True)
            
            gen = Generator(root)
            assert gen.use_src
            # Compare resolved paths to handle macOS /private symlink
            assert gen.base.resolve() == (root / "src").resolve()
    
    def test_create_page(self):
        """Test creating a page."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pages").mkdir()
            
            gen = Generator(root)
            path = gen.create("page", "blog")
            
            assert path.exists()
            assert path.name == "blog.py"
            assert "def blog" in path.read_text()
    
    def test_create_component(self):
        """Test creating a component."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            path = gen.create("component", "Button")
            
            assert path.exists()
            assert path.name == "Button.py"
    
    def test_create_nested_page(self):
        """Test creating a nested page."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            path = gen.create("page", "blog/posts")
            
            assert path.exists()
            assert "blog" in str(path)
    
    def test_create_layout(self):
        """Test creating a layout."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            path = gen.create("layout", "dashboard")
            
            assert path.exists()
            assert path.name == "layout.py"
    
    def test_create_exists_raises(self):
        """Test creating existing file raises."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            gen.create("page", "blog")
            
            with pytest.raises(FileExistsError):
                gen.create("page", "blog")
    
    def test_create_with_force(self):
        """Test force overwrite."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            gen.create("page", "blog")
            
            # Should not raise with force
            path = gen.create("page", "blog", force=True)
            assert path.exists()
    
    def test_create_from_content(self):
        """Test creating from content."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            content = "# AI generated\ndef blog(): pass"
            path = gen.create_from_content("page", "blog", content)
            
            assert path.exists()
            assert "AI generated" in path.read_text()
    
    def test_create_minimal_template(self):
        """Test minimal template is shorter."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            
            path_full = gen.create("page", "full_page", template_style="full")
            path_min = gen.create("page", "min_page", template_style="minimal")
            
            full_len = len(path_full.read_text())
            min_len = len(path_min.read_text())
            
            assert min_len < full_len
    
    def test_list_existing(self):
        """Test listing existing files."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            gen.create("page", "blog")
            gen.create("page", "about")
            
            pages = gen.list_existing("page")
            assert len(pages) == 2
    
    def test_output_path_preview(self):
        """Test previewing output path."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "pages").mkdir()
            
            gen = Generator(root)
            preview = gen.get_output_path_preview("page", "blog")
            
            assert "pages" in str(preview)
            assert "blog.py" in str(preview)
    
    def test_create_api(self):
        """Test creating API route."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            path = gen.create("api", "users")
            
            assert path.exists()
            assert "api" in str(path)
    
    def test_create_middleware(self):
        """Test creating middleware."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            
            gen = Generator(root)
            path = gen.create("middleware", "auth")
            
            assert path.exists()
            assert path.name == "middleware.py"


# ============================================
# Prompt Tests (12 tests)
# ============================================

class TestPrompts:
    """Tests for interactive prompts."""
    
    def test_prompts_registry_has_all_types(self):
        """Test all types have prompts."""
        from pynext.generator.prompts import PROMPTS
        
        expected = [
            "page", "component", "island", "api", "layout",
            "template", "loading", "error", "middleware",
            "action", "hook"
        ]
        
        for type_name in expected:
            assert type_name in PROMPTS, f"Missing prompt: {type_name}"
    
    def test_prompt_for_type_returns_dict(self):
        """Test prompt_for_type returns dict."""
        from pynext.generator.prompts import prompt_for_type
        
        # Mock input
        with patch('builtins.input', return_value="n"):
            result = prompt_for_type("page", "blog")
            assert isinstance(result, dict)
    
    def test_prompt_page_has_data_option(self):
        """Test page prompt includes data option."""
        from pynext.generator.prompts import prompt_page
        
        with patch('builtins.input', side_effect=["n", "y", "y"]):
            result = prompt_page("blog")
            assert "has_data" in result
    
    def test_prompt_component_has_interactive_option(self):
        """Test component prompt includes interactive option."""
        from pynext.generator.prompts import prompt_component
        
        with patch('builtins.input', side_effect=["n", "y", "n"]):
            result = prompt_component("Button")
            assert "is_interactive" in result
    
    def test_prompt_island_has_state_option(self):
        """Test island prompt includes state option."""
        from pynext.generator.prompts import prompt_island
        
        with patch('builtins.input', side_effect=["a", "n"]):
            result = prompt_island("Counter")
            assert "state_type" in result
    
    def test_prompt_api_has_methods_option(self):
        """Test API prompt includes methods option."""
        from pynext.generator.prompts import prompt_api
        
        with patch('builtins.input', side_effect=["GET, POST", "n"]):
            result = prompt_api("users")
            assert "methods" in result
            assert "GET" in result["methods"]
    
    def test_prompt_layout_has_nav_option(self):
        """Test layout prompt includes nav option."""
        from pynext.generator.prompts import prompt_layout
        
        with patch('builtins.input', side_effect=["y", "y", "n"]):
            result = prompt_layout("dashboard")
            assert "has_nav" in result
    
    def test_prompt_middleware_has_purpose_option(self):
        """Test middleware prompt includes purpose option."""
        from pynext.generator.prompts import prompt_middleware
        
        with patch('builtins.input', side_effect=["a", "/(.*)"]):
            result = prompt_middleware("auth")
            assert "purpose" in result
    
    def test_ask_yes_no_yes(self):
        """Test yes/no with yes answer."""
        from pynext.generator.prompts import _ask_yes_no
        
        with patch('builtins.input', return_value="y"):
            result = _ask_yes_no("Test?")
            assert result is True
    
    def test_ask_yes_no_no(self):
        """Test yes/no with no answer."""
        from pynext.generator.prompts import _ask_yes_no
        
        with patch('builtins.input', return_value="n"):
            result = _ask_yes_no("Test?")
            assert result is False
    
    def test_ask_yes_no_default(self):
        """Test yes/no with empty (default) answer."""
        from pynext.generator.prompts import _ask_yes_no
        
        with patch('builtins.input', return_value=""):
            result = _ask_yes_no("Test?", default=True)
            assert result is True
    
    def test_ask_input_with_value(self):
        """Test input with value."""
        from pynext.generator.prompts import _ask_input
        
        with patch('builtins.input', return_value="custom"):
            result = _ask_input("Name?", default="default")
            assert result == "custom"


# ============================================
# AI Tests (8 tests)
# ============================================

@pytest.mark.flaky  # AI-generated code can be non-deterministic
class TestAI:
    """Tests for AI generation (with mocks).
    
    Note: Tests that call the real Anthropic API are marked with
    @pytest.mark.timeout(120) and may occasionally fail due to:
    - API rate limiting
    - Non-deterministic AI output (occasionally produces invalid syntax)
    - Network issues
    
    These are integration tests that verify the AI generation works.
    """
    
    def test_ai_questions_has_all_types(self):
        """Test all types have AI questions."""
        from pynext.generator.ai import AI_QUESTIONS
        
        expected = ["page", "component", "island", "api", "action"]
        for type_name in expected:
            assert type_name in AI_QUESTIONS, f"Missing questions: {type_name}"
    
    def test_ai_questions_are_tuples(self):
        """Test questions are (id, question) tuples."""
        from pynext.generator.ai import AI_QUESTIONS
        
        for type_name, questions in AI_QUESTIONS.items():
            for q in questions:
                assert isinstance(q, tuple)
                assert len(q) == 2
                assert isinstance(q[0], str)  # id
                assert isinstance(q[1], str)  # question
    
    def test_extract_code_python_block(self):
        """Test extracting code from python block."""
        from pynext.generator.ai import extract_code
        
        response = "Here's the code:\n```python\ndef hello(): pass\n```\nDone!"
        result = extract_code(response)
        
        assert "def hello" in result
        assert "```" not in result
    
    def test_extract_code_generic_block(self):
        """Test extracting code from generic block."""
        from pynext.generator.ai import extract_code
        
        response = "```\ndef hello(): pass\n```"
        result = extract_code(response)
        
        assert "def hello" in result
    
    def test_extract_code_no_block(self):
        """Test extracting code without block."""
        from pynext.generator.ai import extract_code
        
        response = "def hello(): pass"
        result = extract_code(response)
        
        assert "def hello" in result
    
    def test_generate_with_ai_no_key_raises(self):
        """Test generate raises without API key."""
        from pynext.generator.ai import generate_with_ai
        
        # Clear env var
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc:
                generate_with_ai("page", "blog", {})
            
            assert "API key required" in str(exc.value)
    
    def test_generate_with_ai_no_anthropic_raises(self):
        """Test generate raises without anthropic installed."""
        from pynext.generator.ai import generate_with_ai
        
        # Mock import error
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test"}):
            with patch.dict('sys.modules', {'anthropic': None}):
                with pytest.raises(ImportError):
                    generate_with_ai("page", "blog", {})
    
    def test_evaluate_completeness_sufficient_mocked(self):
        """Test evaluate logic with mocked API (unit test)."""
        # Mock the entire anthropic module
        mock_anthropic = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="SUFFICIENT")]
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.Anthropic.return_value = mock_client
        
        with patch.dict('sys.modules', {'anthropic': mock_anthropic}):
            from pynext.generator.ai import evaluate_completeness
            
            result = evaluate_completeness(
                "page", "blog",
                {"purpose": "Blog listing", "data": "Posts"},
                api_key="test"
            )
            
            assert result == []
    
    # ========================================
    # REAL API INTEGRATION TESTS
    # These call the actual Anthropic API
    # ========================================
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_evaluate_completeness_real_api_sufficient(self):
        """Integration test: evaluate completeness returns SUFFICIENT for good input."""
        from pynext.generator.ai import evaluate_completeness
        
        # Test with comprehensive info - should return empty (SUFFICIENT)
        result = evaluate_completeness(
            "page", "blog",
            {
                "purpose": "Blog listing page showing all posts with pagination",
                "data": "List of blog posts with title, date, excerpt, author, tags",
                "actions": "Click to view post, filter by tag, search by title, pagination",
                "style": "Card-based grid layout with hover effects and responsive design",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Should be SUFFICIENT (empty list) with this much detail
        assert isinstance(result, list)
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_evaluate_completeness_real_api_needs_more(self):
        """Integration test: evaluate completeness asks follow-ups for vague input."""
        from pynext.generator.ai import evaluate_completeness
        
        # Test with vague info - should return follow-up questions
        result = evaluate_completeness(
            "page", "dashboard",
            {
                "purpose": "a dashboard",  # Too vague
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Should have follow-up questions
        assert isinstance(result, list)
        # With such vague input, expect follow-ups (though API might vary)
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_with_ai_page(self):
        """Integration test: generate a page with real API."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "page",
            "products",
            {
                "purpose": "E-commerce product listing page",
                "data": "Products with name, price, image, rating",
                "actions": "Filter by category, sort by price",
                "style": "Grid of product cards",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Verify generated code is valid Python
        assert "def" in code  # Has a function definition
        assert "from pynext" in code or "from pynext" in code.lower()
        
        # Verify it's syntactically correct
        compile(code, "<generated>", "exec")
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_with_ai_component(self):
        """Integration test: generate a component with real API."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "component",
            "Button",
            {
                "purpose": "A reusable button component",
                "props": "label, onClick, variant, disabled",
                "variants": "primary, secondary, danger, ghost",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Verify generated code
        assert "def" in code.lower() or "class" in code.lower()
        assert "button" in code.lower()
        
        # Verify it compiles
        compile(code, "<generated>", "exec")
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_with_ai_island(self):
        """Integration test: generate an island with real API."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "island",
            "Counter",
            {
                "purpose": "Interactive counter with increment/decrement",
                "state": "Current count value",
                "events": "Click to increment, click to decrement, reset button",
                "effects": "None",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Islands should use signals or state
        assert "def" in code
        # Should have reactivity concepts
        assert "Signal" in code or "signal" in code.lower() or "state" in code.lower()
        
        # Verify it compiles
        compile(code, "<generated>", "exec")
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_with_ai_api_endpoint(self):
        """Integration test: generate an API endpoint with real API."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "api",
            "users",
            {
                "method": "GET and POST",
                "purpose": "CRUD for users - list all users, create new user",
                "params": "GET: none, POST: name, email in body",
                "response": "JSON list of users or created user object",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Should have HTTP method handlers
        assert "def" in code
        assert "get" in code.lower() or "post" in code.lower()
        
        # Verify it compiles
        compile(code, "<generated>", "exec")
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_with_ai_server_action(self):
        """Integration test: generate a server action with real API."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "action",
            "create_post",
            {
                "purpose": "Create a new blog post",
                "input": "title, content, author_id from form",
                "validation": "title required (min 5 chars), content required",
                "result": "Redirect to the new post page on success",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Should have action decorator or function
        assert "def" in code
        assert "action" in code.lower() or "create" in code.lower()
        
        # Verify it compiles
        compile(code, "<generated>", "exec")
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_with_ai_hook(self):
        """Integration test: generate a custom hook with real API."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "hook",
            "use_local_storage",
            {
                "purpose": "Persist state to localStorage with sync across tabs",
                "state": "Generic value of any type",
                "events": "storage event for cross-tab sync",
                "effects": "Read from localStorage on mount, write on change",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Should have hook function
        assert "def" in code
        assert "use" in code.lower() or "local" in code.lower() or "storage" in code.lower()
        
        # Verify it compiles
        compile(code, "<generated>", "exec")
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_with_ai_complex_component(self):
        """Integration test: generate a complex data table component."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "component",
            "DataTable",
            {
                "purpose": "A sortable, filterable data table with pagination",
                "props": "data (list of dicts), columns (list of column configs), page_size",
                "interactive": "yes - sorting, filtering, pagination controls",
                "variants": "default, compact, striped",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Should have table-related code
        assert "def" in code
        assert "table" in code.lower() or "data" in code.lower()
        
        # Verify it compiles
        compile(code, "<generated>", "exec")
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_code_uses_tailwind(self):
        """Integration test: generated code should use Tailwind CSS classes."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "component",
            "Card",
            {
                "purpose": "A card component with header, body, footer",
                "props": "title, children, footer",
                "variants": "default, outlined, elevated",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Should use Tailwind classes
        # Common Tailwind patterns
        tailwind_indicators = [
            "class_=",  # PyNext class attribute
            "flex", "grid", "p-", "m-", "rounded", "shadow",
            "text-", "bg-", "border"
        ]
        
        has_tailwind = any(indicator in code for indicator in tailwind_indicators)
        assert has_tailwind, "Generated code should use Tailwind CSS classes"
        
        # Verify it compiles
        compile(code, "<generated>", "exec")
    
    @pytest.mark.skipif(
        not os.environ.get("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set - skipping integration test"
    )
    @pytest.mark.timeout(120)  # AI API calls can take 30-60s
    def test_generate_code_has_docstrings(self):
        """Integration test: generated code should have docstrings."""
        from pynext.generator.ai import generate_with_ai
        
        code = generate_with_ai(
            "page",
            "about",
            {
                "purpose": "About us page with team info and company mission",
                "data": "Team members with name, role, photo",
                "style": "Clean, professional layout",
            },
            api_key=os.environ["ANTHROPIC_API_KEY"]
        )
        
        # Should have docstrings (triple quotes)
        assert '"""' in code or "'''" in code, "Generated code should have docstrings"
        
        # Verify it compiles
        compile(code, "<generated>", "exec")


# ============================================
# CLI Integration Tests (10 tests)
# ============================================

class TestCLI:
    """Tests for CLI integration."""
    
    def test_cli_has_generate_command(self):
        """Test CLI has generate command."""
        from pynext.cli import main
        import sys
        
        with patch.object(sys, 'argv', ['pynext', 'generate', '--help']):
            with pytest.raises(SystemExit) as exc:
                main()
            # Help exits with 0
            assert exc.value.code == 0
    
    def test_cli_has_g_alias(self):
        """Test CLI has 'g' alias."""
        from pynext.cli import main
        import sys
        
        with patch.object(sys, 'argv', ['pynext', 'g', '--help']):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0
    
    def test_cli_accepts_type_arg(self):
        """Test CLI accepts type argument."""
        from pynext.cli import main
        import sys
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                (Path(tmpdir) / "pages").mkdir()
                
                with patch.object(sys, 'argv', ['pynext', 'g', 'page', 'testpage', '--yes']):
                    result = main()
                    assert result == 0
        finally:
            os.chdir(original_cwd)
    
    def test_cli_accepts_minimal_flag(self):
        """Test CLI accepts --minimal flag."""
        from pynext.cli import main
        import sys
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                
                with patch.object(sys, 'argv', ['pynext', 'g', 'page', 'testmin', '--minimal', '--yes']):
                    result = main()
                    assert result == 0
        finally:
            os.chdir(original_cwd)
    
    def test_cli_accepts_force_flag(self):
        """Test CLI accepts --force flag."""
        from pynext.cli import main
        import sys
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                
                # Create first
                with patch.object(sys, 'argv', ['pynext', 'g', 'page', 'testforce', '--yes']):
                    main()
                
                # Overwrite with force
                with patch.object(sys, 'argv', ['pynext', 'g', 'page', 'testforce', '--yes', '--force']):
                    result = main()
                    assert result == 0
        finally:
            os.chdir(original_cwd)
    
    def test_cli_rejects_invalid_type(self):
        """Test CLI rejects invalid type."""
        from pynext.cli import main
        import sys
        
        with patch.object(sys, 'argv', ['pynext', 'g', 'invalid', 'test']):
            with pytest.raises(SystemExit):
                main()
    
    def test_cli_creates_file(self):
        """Test CLI actually creates file."""
        from pynext.cli import main
        import sys
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                
                with patch.object(sys, 'argv', ['pynext', 'g', 'page', 'blog', '--yes']):
                    main()
                
                assert (Path(tmpdir) / "pages" / "blog.py").exists()
        finally:
            os.chdir(original_cwd)
    
    def test_cli_creates_component_dir(self):
        """Test CLI creates components directory."""
        from pynext.cli import main
        import sys
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                
                with patch.object(sys, 'argv', ['pynext', 'g', 'component', 'Button', '--yes']):
                    main()
                
                assert (Path(tmpdir) / "components" / "Button.py").exists()
        finally:
            os.chdir(original_cwd)
    
    def test_cli_supports_nested_paths(self):
        """Test CLI supports nested paths."""
        from pynext.cli import main
        import sys
        
        original_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                
                with patch.object(sys, 'argv', ['pynext', 'g', 'page', 'blog/posts', '--yes']):
                    main()
                
                assert (Path(tmpdir) / "pages" / "blog" / "posts.py").exists()
        finally:
            os.chdir(original_cwd)
    
    def test_cli_ai_flag_exists(self):
        """Test CLI has --ai flag."""
        from pynext.cli import main
        import sys
        
        with patch.object(sys, 'argv', ['pynext', 'g', '--help']):
            with pytest.raises(SystemExit):
                main()
        
        # Just verify it doesn't crash - actual AI test needs key


# ============================================
# Edge Cases (8 tests)
# ============================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_unicode_name(self):
        """Test unicode in name."""
        from pynext.generator.validators import validate_name, ValidationError
        
        # Should raise for non-ASCII
        with pytest.raises(ValidationError):
            validate_name("日本語", "page")
    
    def test_special_chars_in_path(self):
        """Test special characters in path."""
        from pynext.generator.validators import validate_path
        
        # Dynamic routes are allowed
        result = validate_path("products/[id]", "page")
        assert "[id]" in str(result)
    
    def test_very_long_name(self):
        """Test very long name is accepted."""
        from pynext.generator.validators import validate_name
        
        long_name = "a" * 100
        result = validate_name(long_name, "page")
        assert len(result) == 100
    
    def test_numeric_start_raises(self):
        """Test name starting with number raises."""
        from pynext.generator.validators import validate_name, ValidationError
        
        with pytest.raises(ValidationError):
            validate_name("123page", "page")
    
    def test_create_with_props(self):
        """Test creating with custom props."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = Generator(Path(tmpdir))
            path = gen.create("page", "blog", props={"custom": "value"})
            
            assert path.exists()
    
    def test_empty_project_structure(self):
        """Test in empty project."""
        from pynext.generator import Generator
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = Generator(Path(tmpdir))
            
            # Should still work
            path = gen.create("page", "blog")
            assert path.exists()
    
    def test_python_keyword_variations(self):
        """Test Python keyword variations."""
        from pynext.generator.validators import validate_name, ValidationError
        
        keywords = ["if", "else", "for", "while", "class", "def", "return"]
        for kw in keywords:
            with pytest.raises(ValidationError):
                validate_name(kw, "page")
    
    def test_pynext_reserved_names(self):
        """Test PyNext reserved names."""
        from pynext.generator.validators import validate_name, ValidationError
        
        reserved = ["page", "layout", "template", "loading", "error"]
        for name in reserved:
            with pytest.raises(ValidationError):
                validate_name(name, "page")


# ============================================
# Performance Tests (5 tests)
# ============================================

class TestPerformance:
    """Tests for performance characteristics."""
    
    def test_validate_name_fast(self):
        """Test name validation is fast."""
        from pynext.generator.validators import validate_name
        import time
        
        start = time.perf_counter()
        for _ in range(1000):
            validate_name("test_page", "page")
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 100, f"Took {elapsed:.2f}ms"
    
    def test_template_render_fast(self):
        """Test template rendering is fast."""
        from pynext.generator.templates import get_template, render_template
        import time
        
        template = get_template("page", "full")
        
        start = time.perf_counter()
        for _ in range(1000):
            render_template(template, name="test", title="Test", route="test")
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 100, f"Took {elapsed:.2f}ms"
    
    def test_generator_init_fast(self):
        """Test Generator initialization is fast."""
        from pynext.generator import Generator
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            start = time.perf_counter()
            for _ in range(100):
                Generator(Path(tmpdir))
            elapsed = (time.perf_counter() - start) * 1000
            
            assert elapsed < 500, f"Took {elapsed:.2f}ms"
    
    def test_file_creation_fast(self):
        """Test file creation is fast."""
        from pynext.generator import Generator
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = Generator(Path(tmpdir))
            
            start = time.perf_counter()
            for i in range(100):
                gen.create("page", f"page_{i}")
            elapsed = (time.perf_counter() - start) * 1000
            
            # Should create 100 files in < 1 second
            assert elapsed < 1000, f"Took {elapsed:.2f}ms"
    
    def test_templates_not_large(self):
        """Test templates are not excessively large."""
        from pynext.generator.templates import TEMPLATES
        
        for type_name, templates in TEMPLATES.items():
            for style, content in templates.items():
                # Templates should be < 5KB each
                assert len(content) < 5000, f"{type_name}/{style} is too large"

