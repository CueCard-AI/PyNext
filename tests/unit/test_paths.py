"""
Comprehensive tests for Path Resolution.

Tests:
- ProjectPaths dataclass
- resolve_paths() auto-detection
- detect_structure() structure detection
- get_watch_dirs() for hot reload
- ensure_structure() directory creation
- find_project_root() project root discovery
- validate_structure() validation
- get_page_url() URL generation
"""

import pytest
from pathlib import Path

from pynext.core.paths import (
    ProjectPaths,
    resolve_paths,
    detect_structure,
    get_watch_dirs,
    ensure_structure,
    find_project_root,
    validate_structure,
    get_page_url,
)


# =============================================================================
# ProjectPaths Tests
# =============================================================================

class TestProjectPaths:
    """Tests for ProjectPaths dataclass."""
    
    def test_uses_src_true(self):
        """uses_src is True when pages contains 'src'."""
        paths = ProjectPaths(
            pages=Path("/project/src/pages"),
            components=Path("/project/src/components"),
            lib=Path("/project/src/lib"),
            public=Path("/project/public"),
            root=Path("/project"),
        )
        assert paths.uses_src is True
    
    def test_uses_src_false(self):
        """uses_src is False for standard structure."""
        paths = ProjectPaths(
            pages=Path("/project/pages"),
            components=Path("/project/components"),
            lib=Path("/project/lib"),
            public=Path("/project/public"),
            root=Path("/project"),
        )
        assert paths.uses_src is False
    
    def test_styles_property_src(self):
        """styles property for src structure."""
        paths = ProjectPaths(
            pages=Path("/project/src/pages"),
            components=Path("/project/src/components"),
            lib=Path("/project/src/lib"),
            public=Path("/project/public"),
            root=Path("/project"),
        )
        assert paths.styles == Path("/project/src/styles")
    
    def test_styles_property_standard(self):
        """styles property for standard structure."""
        paths = ProjectPaths(
            pages=Path("/project/pages"),
            components=Path("/project/components"),
            lib=Path("/project/lib"),
            public=Path("/project/public"),
            root=Path("/project"),
        )
        assert paths.styles == Path("/project/styles")
    
    def test_api_property(self):
        """api property returns pages/api."""
        paths = ProjectPaths(
            pages=Path("/project/pages"),
            components=Path("/project/components"),
            lib=Path("/project/lib"),
            public=Path("/project/public"),
            root=Path("/project"),
        )
        assert paths.api == Path("/project/pages/api")
    
    def test_relative_method(self):
        """relative() returns path relative to root."""
        paths = ProjectPaths(
            pages=Path("/project/pages"),
            components=Path("/project/components"),
            lib=Path("/project/lib"),
            public=Path("/project/public"),
            root=Path("/project"),
        )
        result = paths.relative(Path("/project/pages/about/page.py"))
        assert result == Path("pages/about/page.py")
    
    def test_relative_outside_root(self):
        """relative() returns original path if outside root."""
        paths = ProjectPaths(
            pages=Path("/project/pages"),
            components=Path("/project/components"),
            lib=Path("/project/lib"),
            public=Path("/project/public"),
            root=Path("/project"),
        )
        outside = Path("/other/path/file.py")
        result = paths.relative(outside)
        assert result == outside
    
    def test_to_dict(self):
        """to_dict() returns serializable dictionary."""
        paths = ProjectPaths(
            pages=Path("/project/pages"),
            components=Path("/project/components"),
            lib=Path("/project/lib"),
            public=Path("/project/public"),
            root=Path("/project"),
        )
        result = paths.to_dict()
        
        assert isinstance(result, dict)
        assert "pages" in result
        assert "uses_src" in result
        assert isinstance(result["pages"], str)


# =============================================================================
# resolve_paths() Tests
# =============================================================================

class TestResolvePaths:
    """Tests for resolve_paths() function."""
    
    def test_detects_src_structure(self, tmp_path):
        """Detects src/ structure when it exists."""
        (tmp_path / "src" / "pages").mkdir(parents=True)
        
        paths = resolve_paths(tmp_path)
        
        assert paths.uses_src is True
        assert "src" in str(paths.pages)
    
    def test_detects_standard_structure(self, tmp_path):
        """Detects standard structure when no src/."""
        (tmp_path / "pages").mkdir()
        
        paths = resolve_paths(tmp_path)
        
        assert paths.uses_src is False
        assert "src" not in str(paths.pages)
    
    def test_prefers_src_over_root_pages(self, tmp_path):
        """Prefers src/pages when both exist."""
        (tmp_path / "pages").mkdir()
        (tmp_path / "src" / "pages").mkdir(parents=True)
        
        paths = resolve_paths(tmp_path)
        
        assert paths.uses_src is True
    
    def test_returns_absolute_paths(self, tmp_path):
        """Returns absolute paths."""
        (tmp_path / "pages").mkdir()
        
        paths = resolve_paths(tmp_path)
        
        assert paths.pages.is_absolute()
        assert paths.components.is_absolute()
        assert paths.public.is_absolute()
    
    def test_public_always_at_root(self, tmp_path):
        """public/ is always at project root, not in src/."""
        (tmp_path / "src" / "pages").mkdir(parents=True)
        
        paths = resolve_paths(tmp_path)
        
        assert paths.public == tmp_path / "public"
        assert "src" not in str(paths.public)


# =============================================================================
# detect_structure() Tests
# =============================================================================

class TestDetectStructure:
    """Tests for detect_structure() function."""
    
    def test_returns_src_for_src_structure(self, tmp_path):
        """Returns 'src' for src/ structure."""
        (tmp_path / "src" / "pages").mkdir(parents=True)
        
        result = detect_structure(tmp_path)
        
        assert result == "src"
    
    def test_returns_standard_for_standard_structure(self, tmp_path):
        """Returns 'standard' for standard structure."""
        (tmp_path / "pages").mkdir()
        
        result = detect_structure(tmp_path)
        
        assert result == "standard"
    
    def test_returns_standard_for_empty(self, tmp_path):
        """Returns 'standard' for empty directory."""
        result = detect_structure(tmp_path)
        
        assert result == "standard"


# =============================================================================
# get_watch_dirs() Tests
# =============================================================================

class TestGetWatchDirs:
    """Tests for get_watch_dirs() function."""
    
    def test_returns_existing_dirs(self, tmp_path):
        """Returns only existing directories."""
        (tmp_path / "pages").mkdir()
        (tmp_path / "public").mkdir()
        # Don't create components or lib
        
        dirs = get_watch_dirs(tmp_path)
        
        assert tmp_path / "pages" in dirs
        assert tmp_path / "public" in dirs
        assert tmp_path / "components" not in dirs
    
    def test_includes_all_dirs_when_exist(self, tmp_path):
        """Includes all directories when they exist."""
        (tmp_path / "pages").mkdir()
        (tmp_path / "components").mkdir()
        (tmp_path / "lib").mkdir()
        (tmp_path / "public").mkdir()
        (tmp_path / "styles").mkdir()
        
        dirs = get_watch_dirs(tmp_path)
        
        assert len(dirs) >= 4
    
    def test_empty_for_empty_project(self, tmp_path):
        """Returns empty list for empty project."""
        dirs = get_watch_dirs(tmp_path)
        
        assert len(dirs) == 0


# =============================================================================
# ensure_structure() Tests
# =============================================================================

class TestEnsureStructure:
    """Tests for ensure_structure() function."""
    
    def test_creates_standard_structure(self, tmp_path):
        """Creates standard directory structure."""
        paths = ensure_structure(tmp_path, use_src=False)
        
        assert (tmp_path / "pages").exists()
        assert (tmp_path / "components").exists()
        assert (tmp_path / "lib").exists()
        assert (tmp_path / "public").exists()
        assert (tmp_path / "styles").exists()
        assert paths.uses_src is False
    
    def test_creates_src_structure(self, tmp_path):
        """Creates src/ directory structure."""
        paths = ensure_structure(tmp_path, use_src=True)
        
        assert (tmp_path / "src" / "pages").exists()
        assert (tmp_path / "src" / "components").exists()
        assert (tmp_path / "src" / "lib").exists()
        assert (tmp_path / "src" / "styles").exists()
        assert (tmp_path / "public").exists()
        assert paths.uses_src is True
    
    def test_idempotent(self, tmp_path):
        """Running twice doesn't fail."""
        ensure_structure(tmp_path, use_src=False)
        paths2 = ensure_structure(tmp_path, use_src=False)
        
        assert paths2.pages.exists()
    
    def test_returns_project_paths(self, tmp_path):
        """Returns ProjectPaths object."""
        paths = ensure_structure(tmp_path, use_src=False)
        
        assert isinstance(paths, ProjectPaths)
        assert paths.root == tmp_path


# =============================================================================
# find_project_root() Tests
# =============================================================================

class TestFindProjectRoot:
    """Tests for find_project_root() function."""
    
    def test_finds_by_pynext_config(self, tmp_path):
        """Finds root by pynext.config.py."""
        (tmp_path / "pynext.config.py").write_text("# config")
        subdir = tmp_path / "src" / "pages" / "dashboard"
        subdir.mkdir(parents=True)
        
        result = find_project_root(subdir)
        
        assert result == tmp_path
    
    def test_finds_by_pages_directory(self, tmp_path):
        """Finds root by pages/ with page.py files."""
        pages = tmp_path / "pages"
        pages.mkdir()
        (pages / "page.py").write_text("# page")
        
        subdir = tmp_path / "pages"
        
        result = find_project_root(subdir)
        
        assert result == tmp_path
    
    def test_finds_by_src_pages(self, tmp_path):
        """Finds root by src/pages/ directory."""
        (tmp_path / "src" / "pages").mkdir(parents=True)
        
        result = find_project_root(tmp_path / "src" / "pages")
        
        assert result == tmp_path
    
    def test_returns_none_for_no_project(self, tmp_path):
        """Returns None when not in a project."""
        result = find_project_root(tmp_path)
        
        assert result is None
    
    def test_searches_up_hierarchy(self, tmp_path):
        """Searches up the directory hierarchy."""
        (tmp_path / "pynext.config.py").write_text("# config")
        deep = tmp_path / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        
        result = find_project_root(deep)
        
        assert result == tmp_path


# =============================================================================
# validate_structure() Tests
# =============================================================================

class TestValidateStructure:
    """Tests for validate_structure() function."""
    
    def test_valid_project(self, tmp_path):
        """Valid project passes validation."""
        pages = tmp_path / "pages"
        pages.mkdir()
        (pages / "page.py").write_text("# page")
        (tmp_path / "public").mkdir()
        
        valid, issues = validate_structure(tmp_path)
        
        assert valid is True
        assert len(issues) == 0
    
    def test_missing_pages_directory(self, tmp_path):
        """Missing pages directory fails validation."""
        valid, issues = validate_structure(tmp_path)
        
        assert valid is False
        assert any("pages" in issue.lower() for issue in issues)
    
    def test_empty_pages_directory(self, tmp_path):
        """Empty pages directory has issues."""
        (tmp_path / "pages").mkdir()
        # No page.py files
        
        valid, issues = validate_structure(tmp_path)
        
        assert valid is False
        assert any("page.py" in issue.lower() for issue in issues)
    
    def test_missing_public_is_not_an_error(self, tmp_path):
        """Missing public directory doesn't cause validation to fail."""
        pages = tmp_path / "pages"
        pages.mkdir()
        (pages / "page.py").write_text("# page")
        # No public directory - that's OK!
        
        valid, issues = validate_structure(tmp_path)
        
        # Should pass - pages + page.py is all that's required
        assert valid is True
        # No issues for this minimal valid structure
        assert len(issues) == 0


# =============================================================================
# get_page_url() Tests
# =============================================================================

class TestGetPageUrl:
    """Tests for get_page_url() function."""
    
    def test_root_page(self, tmp_path):
        """Root page returns /."""
        (tmp_path / "pages").mkdir()
        page_path = tmp_path / "pages" / "page.py"
        page_path.write_text("# page")
        
        paths = resolve_paths(tmp_path)
        url = get_page_url(page_path, paths)
        
        assert url == "/"
    
    def test_nested_page(self, tmp_path):
        """Nested page returns correct URL."""
        pages = tmp_path / "pages"
        about = pages / "about"
        about.mkdir(parents=True)
        page_path = about / "page.py"
        page_path.write_text("# page")
        
        paths = resolve_paths(tmp_path)
        url = get_page_url(page_path, paths)
        
        assert url == "/about"
    
    def test_deeply_nested_page(self, tmp_path):
        """Deeply nested page returns full path."""
        pages = tmp_path / "pages"
        deep = pages / "blog" / "posts" / "archive"
        deep.mkdir(parents=True)
        page_path = deep / "page.py"
        page_path.write_text("# page")
        
        paths = resolve_paths(tmp_path)
        url = get_page_url(page_path, paths)
        
        assert url == "/blog/posts/archive"
    
    def test_dynamic_route_segment(self, tmp_path):
        """Dynamic route segment preserved."""
        pages = tmp_path / "pages"
        users = pages / "users" / "[id]"
        users.mkdir(parents=True)
        page_path = users / "page.py"
        page_path.write_text("# page")
        
        paths = resolve_paths(tmp_path)
        url = get_page_url(page_path, paths)
        
        assert url == "/users/[id]"
    
    def test_catch_all_route(self, tmp_path):
        """Catch-all route segment preserved."""
        pages = tmp_path / "pages"
        docs = pages / "docs" / "[...slug]"
        docs.mkdir(parents=True)
        page_path = docs / "page.py"
        page_path.write_text("# page")
        
        paths = resolve_paths(tmp_path)
        url = get_page_url(page_path, paths)
        
        assert url == "/docs/[...slug]"


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_symlink_pages_directory(self, tmp_path):
        """Handles symlinked pages directory."""
        real_pages = tmp_path / "real_pages"
        real_pages.mkdir()
        (real_pages / "page.py").write_text("# page")
        
        pages_link = tmp_path / "pages"
        try:
            pages_link.symlink_to(real_pages)
        except OSError:
            pytest.skip("Symlinks not supported")
        
        paths = resolve_paths(tmp_path)
        assert paths.pages.exists()
    
    def test_unicode_path_names(self, tmp_path):
        """Handles unicode in path names."""
        pages = tmp_path / "pages"
        japanese = pages / "日本語"
        japanese.mkdir(parents=True)
        (japanese / "page.py").write_text("# page")
        
        paths = resolve_paths(tmp_path)
        url = get_page_url(japanese / "page.py", paths)
        
        assert "日本語" in url
    
    def test_spaces_in_path(self, tmp_path):
        """Handles spaces in path names."""
        pages = tmp_path / "pages"
        spaced = pages / "my folder"
        spaced.mkdir(parents=True)
        (spaced / "page.py").write_text("# page")
        
        paths = resolve_paths(tmp_path)
        # Should still work
        assert paths.pages.exists()

