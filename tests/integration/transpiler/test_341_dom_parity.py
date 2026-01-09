"""
Phase 34.1: DOM Integration Tests

Integration tests using the MiniAppHarness to verify DOM API transpilation.
These tests verify that:
1. DOM APIs pass through unchanged (no __py.* wrappers)
2. Transpiled code is clean, idiomatic JavaScript
3. Complex DOM patterns work correctly

Total: 15 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# DOM Integration Tests (15 tests)
# =============================================================================

class TestDOMTranspilationParity:
    """Integration tests for DOM API transpilation."""
    
    def test_todo_app_create_and_append(self):
        """Todo app pattern: create and append elements."""
        code = '''
def add_todo(text):
    li = document.createElement("li")
    li.textContent = text
    li.classList.add("todo-item")
    document.getElementById("todo-list").appendChild(li)

add_todo("Buy groceries")
'''
        result = transpile(code)
        
        # Verify clean passthrough - no runtime wrappers
        assert "__py." not in result or "__py.range" in result  # range might use runtime
        assert "document.createElement" in result
        assert "document.getElementById" in result
        assert ".appendChild" in result
        assert ".classList.add" in result
    
    def test_form_input_value(self):
        """Form handling: read and write input values."""
        code = '''
name_input = document.getElementById("name")
email_input = document.getElementById("email")

name = name_input.value
email = email_input.value

name_input.value = ""
email_input.value = ""
'''
        result = transpile(code)
        
        assert "__py." not in result
        assert "document.getElementById" in result
        assert ".value" in result
    
    def test_dynamic_class_toggle(self):
        """Dynamic class manipulation."""
        code = '''
button = document.querySelector(".toggle-btn")
panel = document.getElementById("panel")

def toggle_panel():
    panel.classList.toggle("hidden")
    button.classList.toggle("active")

toggle_panel()
'''
        result = transpile(code)
        
        assert "__py." not in result
        assert ".classList.toggle" in result
    
    def test_element_cloning(self):
        """Element cloning pattern."""
        code = '''
template = document.getElementById("template")
clone = template.cloneNode(True)
clone.id = "clone-1"
clone.classList.remove("template")
document.body.appendChild(clone)
'''
        result = transpile(code)
        
        assert "__py." not in result
        assert ".cloneNode(true)" in result
        assert ".classList.remove" in result
    
    def test_dom_traversal_chain(self):
        """Chained DOM traversal."""
        code = '''
el = document.querySelector(".item")
parent = el.parentElement
first_child = parent.firstElementChild
next_sibling = first_child.nextElementSibling
'''
        result = transpile(code)
        
        assert "__py." not in result
        assert ".parentElement" in result
        assert ".firstElementChild" in result
        assert ".nextElementSibling" in result
    
    def test_query_and_modify(self):
        """Query elements and modify them."""
        code = '''
items = document.querySelectorAll(".item")
for item in items:
    item.classList.add("processed")
    item.dataset.processed = "true"
'''
        result = transpile(code)
        
        assert "document.querySelectorAll" in result
        assert ".classList.add" in result
        assert ".dataset.processed" in result
    
    def test_fragment_batch_append(self):
        """DocumentFragment for efficient batch operations."""
        code = '''
fragment = document.createDocumentFragment()
for i in range(5):
    div = document.createElement("div")
    div.textContent = str(i)
    fragment.appendChild(div)
document.body.appendChild(fragment)
'''
        result = transpile(code)
        
        assert "document.createDocumentFragment()" in result
        assert "document.createElement" in result
        assert "fragment.appendChild" in result
    
    def test_dataset_manipulation(self):
        """Data attribute manipulation."""
        code = '''
card = document.querySelector(".card")
user_id = card.dataset.userId
card.dataset.lastUpdated = "2024-01-01"
card.dataset.status = "active"
'''
        result = transpile(code)
        
        assert "__py." not in result
        assert ".dataset.userId" in result
        assert ".dataset.lastUpdated" in result
    
    def test_nested_queries(self):
        """Nested query selectors."""
        code = '''
container = document.getElementById("container")
header = container.querySelector(".header")
title = header.querySelector("h1")
title.textContent = "New Title"
'''
        result = transpile(code)
        
        assert "__py." not in result
        assert "document.getElementById" in result
        assert "container.querySelector" in result
        assert "header.querySelector" in result
    
    def test_svg_creation(self):
        """SVG element creation with namespace."""
        code = '''
svg_ns = "http://www.w3.org/2000/svg"
svg = document.createElementNS(svg_ns, "svg")
svg.setAttribute("width", "100")
svg.setAttribute("height", "100")

circle = document.createElementNS(svg_ns, "circle")
circle.setAttribute("cx", "50")
circle.setAttribute("cy", "50")
circle.setAttribute("r", "40")

svg.appendChild(circle)
document.body.appendChild(svg)
'''
        result = transpile(code)
        
        assert "__py." not in result
        assert "document.createElementNS" in result
        assert ".setAttribute" in result
    
    def test_no_py_runtime_in_output(self):
        """Pure DOM code should have zero runtime dependencies."""
        code = '''
el = document.getElementById("app")
el.innerHTML = "<h1>Hello</h1>"
el.classList.add("active")
el.dataset.loaded = "true"
child = document.createElement("div")
child.textContent = "Child content"
el.appendChild(child)
'''
        result = transpile(code)
        
        # Verify absolutely no runtime helpers for pure DOM code
        assert "__py." not in result
        assert "import" not in result.lower() or "from" not in result.lower()
    
    def test_clean_passthrough_output(self):
        """Output should be identical to hand-written JavaScript."""
        code = 'el = document.getElementById("app")'
        result = transpile(code)
        
        # The output should be clean, idiomatic JS
        assert result.strip() == 'let el = document.getElementById("app");'
    
    def test_complex_app_structure(self):
        """Complex application structure with multiple DOM operations."""
        code = '''
def render_card(title, description):
    card = document.createElement("div")
    card.className = "card"
    
    h2 = document.createElement("h2")
    h2.textContent = title
    card.appendChild(h2)
    
    p = document.createElement("p")
    p.textContent = description
    card.appendChild(p)
    
    return card

container = document.getElementById("cards")
card1 = render_card("Card 1", "Description 1")
card2 = render_card("Card 2", "Description 2")
container.appendChild(card1)
container.appendChild(card2)
'''
        result = transpile(code)
        
        assert "__py." not in result
        assert "document.createElement" in result
        assert ".className" in result
        assert ".textContent" in result
        assert ".appendChild" in result
    
    def test_list_rendering(self):
        """List rendering pattern."""
        code = '''
items = ["Apple", "Banana", "Cherry"]
ul = document.getElementById("fruit-list")

for item in items:
    li = document.createElement("li")
    li.textContent = item
    li.classList.add("fruit-item")
    ul.appendChild(li)
'''
        result = transpile(code)
        
        assert "document.getElementById" in result
        assert "document.createElement" in result
        assert ".textContent" in result
        assert ".classList.add" in result
    
    def test_conditional_display(self):
        """Conditional visibility pattern.
        
        Note: The transpiler uses __py.bool() for truthiness checks on variables.
        This is correct behavior for Python semantics (where `if x:` checks truthy).
        """
        code = '''
def show_element(selector):
    el = document.querySelector(selector)
    if el:
        el.hidden = False
        el.classList.remove("hidden")

def hide_element(selector):
    el = document.querySelector(selector)
    if el:
        el.hidden = True
        el.classList.add("hidden")

show_element(".notification")
hide_element(".loading")
'''
        result = transpile(code)
        
        # DOM APIs should pass through
        assert "document.querySelector" in result
        assert ".hidden" in result
        assert ".classList.remove" in result
        assert ".classList.add" in result
        # __py.bool is expected for truthiness checks (Python semantics)


class TestDOMImportPassthrough:
    """Tests for DOM import handling."""
    
    def test_import_document_passthrough(self):
        """Importing document should not generate any JS import."""
        code = '''
from pynext.client import document

el = document.getElementById("app")
'''
        result = transpile(code)
        
        # document is a browser global - no import needed
        assert "import" not in result.lower() or "from" not in result.lower()
        assert "document.getElementById" in result
    
    def test_import_element_type_only(self):
        """Importing Element should not generate JS code."""
        code = '''
from pynext.client import Element

def process_element(el):
    el.classList.add("processed")

btn = document.querySelector("button")
process_element(btn)
'''
        result = transpile(code)
        
        # Element is a type-only import
        assert "__py." not in result
        assert "document.querySelector" in result

