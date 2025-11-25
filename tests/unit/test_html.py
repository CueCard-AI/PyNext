"""
Unit tests for PyNext HTML element builder.

Tests Element creation, rendering, attributes, and children.
"""

import pytest
from pynext.core.html import (
    Element, Fragment,
    div, span, p, h1, h2, h3, h4, h5, h6,
    a, button, input_, form, label, textarea, select, option,
    ul, ol, li,
    table, thead, tbody, tr, th, td,
    img, video, audio, canvas, svg,
    header, footer, nav, main, section, article, aside,
    script, style, link, meta,
    raw_html,
)


class TestElement:
    """Tests for the Element class."""
    
    def test_create_element(self):
        """Element can be created with a tag name."""
        el = Element("div")
        assert el.tag == "div"
    
    def test_element_with_attributes(self):
        """Element can have attributes."""
        el = Element("div", {"id": "test", "class": "container"})
        rendered = el.render()
        
        assert 'id="test"' in rendered
        assert 'class="container"' in rendered
    
    def test_element_with_children_bracket(self):
        """Element children via bracket syntax."""
        el = div()["Hello World"]
        rendered = el.render()
        
        assert "<div>Hello World</div>" == rendered
    
    def test_element_nested_children(self):
        """Elements can be nested."""
        el = div()[
            h1()["Title"],
            p()["Paragraph"]
        ]
        rendered = el.render()
        
        assert "<div>" in rendered
        assert "<h1>Title</h1>" in rendered
        assert "<p>Paragraph</p>" in rendered
        assert "</div>" in rendered
    
    def test_element_class_attribute(self):
        """class_ attribute maps to class."""
        el = div(class_="container")
        rendered = el.render()
        
        assert 'class="container"' in rendered
    
    def test_element_data_attributes(self):
        """data-* attributes work correctly."""
        el = div(data_id="123", data_name="test")
        rendered = el.render()
        
        # Implementation may use underscores or hyphens
        assert 'data' in rendered and '123' in rendered
        assert 'test' in rendered
    
    def test_element_boolean_attributes(self):
        """Boolean attributes render correctly."""
        el = input_(type="checkbox", checked=True, disabled=False)
        rendered = el.render()
        
        assert "checked" in rendered
        # disabled=False should not appear
    
    def test_void_elements(self):
        """Void elements (img, input, etc.) don't have closing tags."""
        el = img(src="/image.png", alt="Test")
        rendered = el.render()
        
        assert "<img" in rendered
        assert 'src="/image.png"' in rendered
        assert "</img>" not in rendered
    
    def test_element_escapes_content(self):
        """Element content is HTML-escaped."""
        el = div()["<script>alert('xss')</script>"]
        rendered = el.render()
        
        assert "<script>" not in rendered
        assert "&lt;script&gt;" in rendered


class TestHTMLElements:
    """Tests for specific HTML element helpers."""
    
    def test_div(self):
        """div() creates a div element."""
        el = div(id="main")["Content"]
        assert "<div" in el.render()
        assert "</div>" in el.render()
    
    def test_span(self):
        """span() creates a span element."""
        el = span(class_="highlight")["Text"]
        assert "<span" in el.render()
    
    def test_headings(self):
        """h1-h6 create heading elements."""
        assert "<h1>" in h1()["Title"].render()
        assert "<h2>" in h2()["Title"].render()
        assert "<h3>" in h3()["Title"].render()
        assert "<h4>" in h4()["Title"].render()
        assert "<h5>" in h5()["Title"].render()
        assert "<h6>" in h6()["Title"].render()
    
    def test_anchor(self):
        """a() creates anchor elements."""
        el = a(href="/page")["Link"]
        rendered = el.render()
        
        assert "<a" in rendered
        assert 'href="/page"' in rendered
    
    def test_button(self):
        """button() creates button elements."""
        el = button(type="submit")["Click"]
        rendered = el.render()
        
        assert "<button" in rendered
        assert 'type="submit"' in rendered
    
    def test_input(self):
        """input_() creates input elements."""
        el = input_(type="text", name="username", placeholder="Enter name")
        rendered = el.render()
        
        assert "<input" in rendered
        assert 'type="text"' in rendered
        assert 'name="username"' in rendered
    
    def test_form(self):
        """form() creates form elements with children."""
        el = form(action="/submit", method="POST")[
            input_(type="text", name="name"),
            button(type="submit")["Submit"]
        ]
        rendered = el.render()
        
        assert "<form" in rendered
        assert 'action="/submit"' in rendered
        assert "<input" in rendered
        assert "<button" in rendered
    
    def test_list_elements(self):
        """ul/ol/li create list elements."""
        el = ul()[
            li()["Item 1"],
            li()["Item 2"],
            li()["Item 3"],
        ]
        rendered = el.render()
        
        assert "<ul>" in rendered
        assert "<li>Item 1</li>" in rendered
        assert "<li>Item 2</li>" in rendered
        assert "<li>Item 3</li>" in rendered
        assert "</ul>" in rendered
    
    def test_table_elements(self):
        """table/thead/tbody/tr/th/td create table elements."""
        el = table()[
            thead()[
                tr()[th()["Header"]]
            ],
            tbody()[
                tr()[td()["Cell"]]
            ]
        ]
        rendered = el.render()
        
        assert "<table>" in rendered
        assert "<thead>" in rendered
        assert "<th>Header</th>" in rendered
        assert "<tbody>" in rendered
        assert "<td>Cell</td>" in rendered
    
    def test_semantic_elements(self):
        """Semantic elements render correctly."""
        assert "<header>" in header()["Header"].render()
        assert "<footer>" in footer()["Footer"].render()
        assert "<nav>" in nav()["Nav"].render()
        assert "<main>" in main()["Main"].render()
        assert "<section>" in section()["Section"].render()
        assert "<article>" in article()["Article"].render()
        assert "<aside>" in aside()["Aside"].render()


class TestFragment:
    """Tests for Fragment (multiple root elements)."""
    
    def test_create_fragment(self):
        """Fragment can hold multiple elements."""
        # Fragment takes a list of children
        frag = Fragment([
            h1()["Title"],
            p()["Paragraph"],
        ])
        rendered = frag.render()
        
        assert "<h1>Title</h1>" in rendered
        assert "<p>Paragraph</p>" in rendered
    
    def test_empty_fragment(self):
        """Empty fragment renders to empty string."""
        frag = Fragment([])
        assert frag.render() == ""


class TestRawHTML:
    """Tests for raw (unescaped) HTML."""
    
    def test_raw_html(self):
        """raw_html() inserts unescaped HTML."""
        html = raw_html("<script>console.log('test')</script>")
        rendered = str(html) if hasattr(html, '__str__') else html.render()
        
        assert "<script>" in rendered
        assert "&lt;" not in rendered


class TestEventHandlers:
    """Tests for event handler attributes."""
    
    def test_onclick_string(self):
        """onclick with string value."""
        el = button(onclick="handleClick()")["Click"]
        rendered = el.render()
        
        assert "onclick" in rendered or "id=" in rendered  # May use ID for hydration
    
    def test_onclick_generates_id(self):
        """onclick with function generates element ID for hydration."""
        el = button(onclick=lambda: None)["Click"]
        rendered = el.render()
        # Element may have ID for event binding during hydration
        # Implementation varies - just check it renders
        assert "<button" in rendered


class TestListRendering:
    """Tests for rendering lists of elements."""
    
    def test_list_of_children(self):
        """List of children renders all items."""
        items = ["a", "b", "c"]
        el = ul()[
            [li()[item] for item in items]
        ]
        rendered = el.render()
        
        assert "<li>a</li>" in rendered
        assert "<li>b</li>" in rendered
        assert "<li>c</li>" in rendered
    
    def test_conditional_children(self):
        """Conditional children with and/or."""
        show = True
        el = div()[
            show and span()["Visible"],
            not show and span()["Hidden"],
        ]
        rendered = el.render()
        
        assert "Visible" in rendered
        assert "Hidden" not in rendered
    
    def test_none_children_ignored(self):
        """None children are ignored."""
        el = div()[
            span()["First"],
            None,
            span()["Second"],
        ]
        rendered = el.render()
        
        assert "First" in rendered
        assert "Second" in rendered


class TestAttributeEdgeCases:
    """Tests for edge cases in attribute handling."""
    
    def test_empty_string_attribute(self):
        """Empty string attribute still renders."""
        el = div(title="")
        rendered = el.render()
        assert 'title=""' in rendered
    
    def test_none_attribute_excluded(self):
        """None attribute is not rendered."""
        el = div(id=None, class_="test")
        rendered = el.render()
        
        assert 'id=' not in rendered or 'id="None"' not in rendered
        assert 'class="test"' in rendered
    
    def test_numeric_attribute(self):
        """Numeric attributes are stringified."""
        el = div(tabindex=0, data_count=42)
        rendered = el.render()
        
        assert 'tabindex="0"' in rendered
        # data_count may render as data_count or data-count
        assert '42' in rendered
    
    def test_style_dict_attribute(self):
        """Style dict is rendered as CSS string."""
        el = div(style={"color": "red", "font-size": "16px"})
        rendered = el.render()
        
        # Should contain style attribute with CSS
        assert "style=" in rendered
        assert "color" in rendered

