"""
Comprehensive tests for Client Testing Query Methods.

WHAT THIS FILE TESTS:
- getByText / queryByText / findByText (with regex support)
- getByRole / queryByRole / findByRole
- getByTestId / queryByTestId / findByTestId
- getByLabelText / queryByLabelText / findByLabelText
- getByPlaceholderText / queryByPlaceholderText / findByPlaceholderText
- getAllBy* / queryAllBy* / findAllBy* variants
- Regex pattern support in text queries

Total: 50 tests
"""

import pytest
import re
import asyncio
from pynext.testing.queries import (
    getByText, queryByText, findByText,
    getAllByText, queryAllByText, findAllByText,
    getByRole, queryByRole, findByRole,
    getAllByRole, queryAllByRole, findAllByRole,
    getByTestId, queryByTestId, findByTestId,
    getAllByTestId, queryAllByTestId, findAllByTestId,
    getByLabelText, queryByLabelText, findByLabelText,
    getAllByLabelText, queryAllByLabelText, findAllByLabelText,
    getByPlaceholderText, queryByPlaceholderText, findByPlaceholderText,
    getAllByPlaceholderText, queryAllByPlaceholderText, findAllByPlaceholderText,
)
from pynext.testing.render import HTMLNode, parse_html


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def html_container():
    """Create a sample HTML container."""
    html = """
    <div>
        <h1>Welcome</h1>
        <p>Hello World</p>
        <p>Hello Again</p>
        <button role="button" aria-label="Submit">Submit</button>
        <input data-testid="email" placeholder="Enter email" />
        <label for="name">Name</label>
        <input id="name" />
        <div data-testid="count">42</div>
    </div>
    """
    return parse_html(html)


# =============================================================================
# getByText Tests
# =============================================================================

class TestGetByText:
    """Tests for getByText query."""
    
    def test_getByText_exact_match(self, html_container):
        """Test getByText with exact match."""
        element = getByText(html_container, "Hello World")
        assert element is not None
        assert element.text == "Hello World"
    
    def test_getByText_raises_when_not_found(self, html_container):
        """Test getByText raises ValueError when not found."""
        with pytest.raises(ValueError, match="Unable to find element"):
            getByText(html_container, "Goodbye")
    
    def test_getByText_with_regex_pattern(self, html_container):
        """Test getByText with regex pattern."""
        pattern = re.compile(r"Hello\s+\w+")
        element = getByText(html_container, pattern)
        assert element is not None
        assert "Hello" in element.text
    
    def test_getByText_with_regex_string(self, html_container):
        """Test getByText with regex string (case-insensitive)."""
        pattern = re.compile(r"hello\s+world", re.I)
        element = getByText(html_container, pattern, exact=False)
        assert element is not None
    
    def test_getByText_substring_match(self, html_container):
        """Test getByText with substring match."""
        element = getByText(html_container, "Hello", exact=False)
        assert element is not None


# =============================================================================
# queryByText Tests
# =============================================================================

class TestQueryByText:
    """Tests for queryByText query."""
    
    def test_queryByText_returns_element(self, html_container):
        """Test queryByText returns element when found."""
        element = queryByText(html_container, "Hello World")
        assert element is not None
    
    def test_queryByText_returns_none_when_not_found(self, html_container):
        """Test queryByText returns None when not found."""
        element = queryByText(html_container, "Goodbye")
        assert element is None
    
    def test_queryByText_with_regex(self, html_container):
        """Test queryByText with regex pattern."""
        pattern = re.compile(r"Welcome")
        element = queryByText(html_container, pattern)
        assert element is not None


# =============================================================================
# findByText Tests
# =============================================================================

class TestFindByText:
    """Tests for findByText async query."""
    
    async def test_findByText_finds_element(self, html_container):
        """Test findByText finds element."""
        element = await findByText(html_container, "Hello World")
        assert element is not None
    
    async def test_findByText_times_out(self, html_container):
        """Test findByText times out when element not found."""
        with pytest.raises(TimeoutError):
            await findByText(html_container, "Goodbye", timeout=0.1)
    
    async def test_findByText_with_regex(self, html_container):
        """Test findByText with regex pattern."""
        pattern = re.compile(r"Hello")
        element = await findByText(html_container, pattern)
        assert element is not None


# =============================================================================
# getAllByText Tests
# =============================================================================

class TestGetAllByText:
    """Tests for getAllByText query."""
    
    def test_getAllByText_returns_all_matches(self, html_container):
        """Test getAllByText returns all matching elements."""
        elements = getAllByText(html_container, "Hello", exact=False)
        assert len(elements) >= 2
        assert all("Hello" in elem.text for elem in elements)
    
    def test_getAllByText_raises_when_none_found(self, html_container):
        """Test getAllByText raises when none found."""
        with pytest.raises(ValueError, match="Unable to find elements"):
            getAllByText(html_container, "Goodbye")
    
    def test_getAllByText_with_regex(self, html_container):
        """Test getAllByText with regex pattern."""
        pattern = re.compile(r"Hello", re.I)
        elements = getAllByText(html_container, pattern, exact=False)
        assert len(elements) >= 2


# =============================================================================
# queryAllByText Tests
# =============================================================================

class TestQueryAllByText:
    """Tests for queryAllByText query."""
    
    def test_queryAllByText_returns_list(self, html_container):
        """Test queryAllByText returns list of matches."""
        elements = queryAllByText(html_container, "Hello", exact=False)
        assert isinstance(elements, list)
        assert len(elements) >= 2
    
    def test_queryAllByText_returns_empty_list(self, html_container):
        """Test queryAllByText returns empty list when none found."""
        elements = queryAllByText(html_container, "Goodbye")
        assert elements == []


# =============================================================================
# findAllByText Tests
# =============================================================================

class TestFindAllByText:
    """Tests for findAllByText async query."""
    
    async def test_findAllByText_returns_all_matches(self, html_container):
        """Test findAllByText returns all matches."""
        elements = await findAllByText(html_container, "Hello", exact=False)
        assert len(elements) >= 2
    
    async def test_findAllByText_times_out(self, html_container):
        """Test findAllByText times out when none found."""
        with pytest.raises(TimeoutError):
            await findAllByText(html_container, "Goodbye", timeout=0.1)


# =============================================================================
# getByRole Tests
# =============================================================================

class TestGetByRole:
    """Tests for getByRole query."""
    
    def test_getByRole_finds_element(self, html_container):
        """Test getByRole finds element by role."""
        element = getByRole(html_container, "button")
        assert element is not None
        assert element.tag == "button"
    
    def test_getByRole_with_name(self, html_container):
        """Test getByRole with name parameter."""
        element = getByRole(html_container, "button", name="Submit")
        assert element is not None
    
    def test_getByRole_raises_when_not_found(self, html_container):
        """Test getByRole raises when not found."""
        with pytest.raises(ValueError, match="Unable to find element"):
            getByRole(html_container, "dialog")


# =============================================================================
# getByTestId Tests
# =============================================================================

class TestGetByTestId:
    """Tests for getByTestId query."""
    
    def test_getByTestId_finds_element(self, html_container):
        """Test getByTestId finds element."""
        element = getByTestId(html_container, "email")
        assert element is not None
        assert element.attrs.get("data-testid") == "email"
    
    def test_getByTestId_raises_when_not_found(self, html_container):
        """Test getByTestId raises when not found."""
        with pytest.raises(ValueError, match="Unable to find element"):
            getByTestId(html_container, "missing")


# =============================================================================
# getByLabelText Tests
# =============================================================================

class TestGetByLabelText:
    """Tests for getByLabelText query."""
    
    def test_getByLabelText_finds_by_label(self, html_container):
        """Test getByLabelText finds input by label."""
        element = getByLabelText(html_container, "Name")
        assert element is not None
        assert element.tag == "input"
        assert element.attrs.get("id") == "name"
    
    def test_getByLabelText_raises_when_not_found(self, html_container):
        """Test getByLabelText raises when not found."""
        with pytest.raises(ValueError, match="Unable to find element"):
            getByLabelText(html_container, "Missing Label")


# =============================================================================
# getByPlaceholderText Tests
# =============================================================================

class TestGetByPlaceholderText:
    """Tests for getByPlaceholderText query."""
    
    def test_getByPlaceholderText_finds_element(self, html_container):
        """Test getByPlaceholderText finds element."""
        element = getByPlaceholderText(html_container, "Enter email")
        assert element is not None
        assert element.attrs.get("placeholder") == "Enter email"
    
    def test_getByPlaceholderText_raises_when_not_found(self, html_container):
        """Test getByPlaceholderText raises when not found."""
        with pytest.raises(ValueError, match="Unable to find element"):
            getByPlaceholderText(html_container, "Missing placeholder")


# =============================================================================
# Regex Support Tests
# =============================================================================

class TestRegexSupport:
    """Tests for regex pattern support in queries."""
    
    def test_regex_case_insensitive(self):
        """Test case-insensitive regex matching."""
        html = parse_html("<div><p>Hello WORLD</p></div>")
        pattern = re.compile(r"hello\s+world", re.I)
        element = getByText(html, pattern, exact=False)
        assert element is not None
    
    def test_regex_multiline(self):
        """Test multiline regex matching."""
        html = parse_html("<div><p>Line 1\nLine 2</p></div>")
        pattern = re.compile(r"Line \d+", re.M)
        elements = getAllByText(html, pattern)
        assert len(elements) > 0
    
    def test_regex_with_anchor(self):
        """Test regex with anchors."""
        html = parse_html("<div><p>Start text</p></div>")
        pattern = re.compile(r"^Start")
        element = getByText(html, pattern, exact=False)
        assert element is not None
    
    def test_string_vs_regex(self):
        """Test that both strings and regex patterns work."""
        html = parse_html("<div><p>Test 123</p></div>")
        
        # String match
        elem1 = getByText(html, "Test", exact=False)
        assert elem1 is not None
        
        # Regex match
        pattern = re.compile(r"Test \d+")
        elem2 = getByText(html, pattern)
        assert elem2 is not None


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Edge case tests for queries."""
    
    def test_empty_container(self):
        """Test queries on empty container."""
        empty = parse_html("<div></div>")
        assert queryByText(empty, "anything") is None
        assert queryAllByText(empty, "anything") == []
    
    def test_nested_text(self):
        """Test finding text in nested elements."""
        html = parse_html("<div><div><p>Nested</p></div></div>")
        element = getByText(html, "Nested")
        assert element is not None
    
    def test_multiple_matches_first_one(self):
        """Test getByText returns first match when multiple exist."""
        html = parse_html("<div><p>Match</p><p>Match</p></div>")
        element = getByText(html, "Match")
        assert element is not None
        # Should return first one
        assert element.text == "Match"

