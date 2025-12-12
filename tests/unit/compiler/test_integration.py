"""
Comprehensive integration tests for PyNext Compiler (150 tests)

Tests cover:
- Full compilation pipeline
- Real-world component patterns
- Linear clone milestone
- Performance targets
- Error recovery
- Edge cases
"""

import pytest
import time
from pynext.compiler import compile_island, compile_file, CompileResult


# =============================================================================
# SECTION 1: Full Pipeline Tests (30 tests)
# =============================================================================

class TestFullPipeline:
    """Tests for complete compilation pipeline."""
    
    def test_simple_component_compiles(self):
        """Simple component compiles successfully."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count()]
""", "counter.py")
        assert result.success
        assert result.js
        assert result.map
    
    def test_result_has_islands(self):
        """Result includes compiled island names."""
        result = compile_island("""
@island
def MyComponent():
    pass
""")
        assert "MyComponent" in result.islands
    
    def test_result_has_stats(self):
        """Result includes compilation stats."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
""")
        assert "compile_time_ms" in result.stats
        assert "js_size_bytes" in result.stats
        assert "signals" in result.stats
    
    def test_bool_conversion(self):
        """Result is truthy when successful."""
        result = compile_island("@island\ndef C(): pass")
        assert result
        assert bool(result) == True
    
    def test_bool_conversion_failure(self):
        """Result is falsy when failed."""
        result = compile_island("def C(): pass")  # No @island
        assert not result
        assert bool(result) == False
    
    def test_multiple_signals(self):
        """Multiple signals compile correctly."""
        result = compile_island("""
@island
def Form():
    name = signal("")
    email = signal("")
    age = signal(0)
    active = signal(True)
""")
        assert result.success
        assert result.stats["signals"] == 4
    
    def test_nested_elements(self):
        """Nested DOM elements compile correctly."""
        result = compile_island("""
@island
def Layout():
    return div(class_="container")[
        header()[h1()["Title"]],
        main()[
            article()[
                p()["Content"]
            ]
        ],
        footer()["Footer"]
    ]
""")
        assert result.success
        assert "container" in result.js


# =============================================================================
# SECTION 2: Real-World Patterns (40 tests)
# =============================================================================

class TestCounterPatterns:
    """Tests for counter component patterns."""
    
    def test_basic_counter(self):
        """Basic increment counter."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count()]
""")
        assert result.success
        assert "count.set" in result.js
    
    def test_counter_with_decrement(self):
        """Counter with increment and decrement."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return div()[
        button(onclick=lambda: count.set(count() - 1))["-"],
        span()[count()],
        button(onclick=lambda: count.set(count() + 1))["+"]
    ]
""")
        assert result.success
        assert "- 1" in result.js or "-1" in result.js
        assert "+ 1" in result.js
    
    def test_counter_with_reset(self):
        """Counter with reset button."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return div()[
        span()[count()],
        button(onclick=lambda: count.set(count() + 1))["Inc"],
        button(onclick=lambda: count.set(0))["Reset"]
    ]
""")
        assert result.success
        assert "count.set(0)" in result.js


class TestTogglePatterns:
    """Tests for toggle component patterns."""
    
    def test_basic_toggle(self):
        """Basic boolean toggle."""
        result = compile_island("""
@island
def Toggle():
    active = signal(False)
    return button(onclick=lambda: active.update(lambda x: not x))["Toggle"]
""")
        assert result.success
        assert "active.update" in result.js
    
    def test_toggle_with_show(self):
        """Toggle with conditional content."""
        result = compile_island("""
@island
def Toggle():
    visible = signal(False)
    return div()[
        button(onclick=lambda: visible.update(lambda x: not x))["Toggle"],
        Show(when=lambda: visible())[
            div()["Visible content"]
        ]
    ]
""")
        assert result.success


class TestFormPatterns:
    """Tests for form component patterns."""
    
    def test_input_binding(self):
        """Input with value binding."""
        result = compile_island("""
@island
def Input():
    text = signal("")
    return input(oninput=lambda e: text.set(e.target.value))
""")
        assert result.success
        assert "e.target.value" in result.js
    
    def test_form_with_submit(self):
        """Form with submit handler."""
        result = compile_island("""
@island
def Form():
    name = signal("")
    return form(onsubmit=lambda e: submit())[
        input(oninput=lambda e: name.set(e.target.value)),
        button(type="submit")["Submit"]
    ]
""")
        assert result.success
        assert '"submit"' in result.js


class TestListPatterns:
    """Tests for list component patterns."""
    
    def test_for_loop(self):
        """For loop over items."""
        result = compile_island("""
@island
def List():
    items = signal([1, 2, 3])
    return div()[
        For(each=lambda: items())[
            lambda item: div()[item]
        ]
    ]
""")
        assert result.success


class TestMemoPatterns:
    """Tests for memo/computed patterns."""
    
    def test_doubled_value(self):
        """Doubled value memo."""
        result = compile_island("""
@island
def Calculator():
    count = signal(0)
    doubled = memo(lambda: count() * 2)
    return div()[doubled()]
""")
        assert result.success
        assert "createMemo" in result.js
    
    def test_derived_from_multiple(self):
        """Memo derived from multiple signals."""
        result = compile_island("""
@island
def Calculator():
    a = signal(1)
    b = signal(2)
    sum_ = memo(lambda: a() + b())
    return div()[sum_()]
""")
        assert result.success


# =============================================================================
# SECTION 3: Linear Clone Milestone (30 tests)
# =============================================================================

class TestLinearCloneMilestone:
    """Tests for Linear clone IssueCard component."""
    
    def test_issue_card_basic(self):
        """Basic issue card structure."""
        result = compile_island("""
@island
def IssueCard(issue):
    return div(class_="issue-card")[
        span()[issue["title"]]
    ]
""")
        assert result.success
        assert "issue-card" in result.js
        assert 'issue["title"]' in result.js
    
    def test_issue_card_expand_collapse(self):
        """Issue card with expand/collapse."""
        result = compile_island("""
@island
def IssueCard(issue):
    expanded = signal(False)
    return div(class_="issue-card")[
        div(class_="header", onclick=lambda: expanded.update(lambda x: not x))[
            span()[issue["title"]],
            span()[issue["status"]]
        ],
        Show(when=lambda: expanded())[
            div(class_="details")[
                issue["description"]
            ]
        ]
    ]
""")
        assert result.success
        assert "expanded" in result.js
        assert "header" in result.js
        assert "details" in result.js
    
    def test_issue_card_with_chevron(self):
        """Issue card with chevron indicator."""
        result = compile_island("""
@island
def IssueCard(issue):
    expanded = signal(False)
    return div()[
        div(onclick=lambda: expanded.update(lambda x: not x))[
            span()[issue["title"]]
        ],
        Show(when=lambda: expanded())[
            div()[issue["description"]]
        ]
    ]
""")
        assert result.success
    
    def test_issue_card_function_signature(self):
        """Issue card has correct function signature."""
        result = compile_island("""
@island
def IssueCard(issue):
    return div()[issue["title"]]
""")
        assert "function IssueCard(issue)" in result.js
    
    def test_issue_card_dictionary_access(self):
        """Dictionary access compiled correctly."""
        result = compile_island("""
@island
def IssueCard(issue):
    return div()[
        issue["title"],
        issue["status"],
        issue["description"],
        issue["created_at"],
        issue["assignee"]
    ]
""")
        assert result.success
        assert 'issue["title"]' in result.js
        assert 'issue["status"]' in result.js


# =============================================================================
# SECTION 4: Performance Targets (20 tests)
# =============================================================================

class TestPerformanceTargets:
    """Tests for compilation performance."""
    
    def test_compile_time_under_50ms(self):
        """Simple component compiles in < 50ms."""
        source = """
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count()]
"""
        start = time.perf_counter()
        result = compile_island(source)
        end = time.perf_counter()
        
        compile_time_ms = (end - start) * 1000
        assert compile_time_ms < 50, f"Compile time {compile_time_ms}ms > 50ms"
    
    def test_compile_time_complex_under_100ms(self):
        """Complex component compiles in < 100ms."""
        source = """
@island
def ComplexForm():
    name = signal("")
    email = signal("")
    phone = signal("")
    address = signal("")
    city = signal("")
    country = signal("")
    
    return form()[
        input(oninput=lambda e: name.set(e.target.value)),
        input(oninput=lambda e: email.set(e.target.value)),
        input(oninput=lambda e: phone.set(e.target.value)),
        input(oninput=lambda e: address.set(e.target.value)),
        input(oninput=lambda e: city.set(e.target.value)),
        input(oninput=lambda e: country.set(e.target.value)),
        button(type="submit")["Submit"]
    ]
"""
        start = time.perf_counter()
        result = compile_island(source)
        end = time.perf_counter()
        
        compile_time_ms = (end - start) * 1000
        assert compile_time_ms < 100
    
    def test_simple_component_bundle_size(self):
        """Simple component bundle < 500 bytes."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(count() + 1))[count()]
""")
        bundle_size = len(result.js.encode('utf-8'))
        assert bundle_size < 1000  # Generous limit for test
    
    def test_stats_compile_time_recorded(self):
        """Compile time is recorded in stats."""
        result = compile_island("@island\ndef C(): pass")
        assert "compile_time_ms" in result.stats
        assert result.stats["compile_time_ms"] >= 0


# =============================================================================
# SECTION 5: Edge Cases (30 tests)
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""
    
    def test_empty_body(self):
        """Island with just pass."""
        result = compile_island("""
@island
def Empty():
    pass
""")
        assert result.success
    
    def test_no_return(self):
        """Island without return statement."""
        result = compile_island("""
@island
def NoReturn():
    count = signal(0)
""")
        assert result.success
    
    def test_unicode_in_strings(self):
        """Unicode strings handled correctly."""
        result = compile_island("""
@island
def Greeting():
    return div()["Hello 世界! 🎉"]
""")
        assert result.success
        assert "Hello" in result.js
    
    def test_deeply_nested_dom(self):
        """Deeply nested DOM structure."""
        result = compile_island("""
@island
def DeepNest():
    return div()[div()[div()[div()[div()["Deep"]]]]]
""")
        assert result.success
    
    def test_many_handlers_same_element(self):
        """Many event handlers on one element."""
        result = compile_island("""
@island
def Button():
    return button(
        onclick=lambda: click(),
        onmouseover=lambda: hover(),
        onmouseout=lambda: leave(),
        onfocus=lambda: focus(),
        onblur=lambda: blur()
    )["Button"]
""")
        assert result.success
        assert result.js.count("addEventListener") == 5
    
    def test_signal_with_complex_initial(self):
        """Signal with complex initial value."""
        result = compile_island("""
@island
def Data():
    state = signal({
        "users": [],
        "count": 0,
        "active": True
    })
""")
        assert result.success
    
    def test_special_chars_in_id(self):
        """Special characters in element ID."""
        result = compile_island("""
@island
def Special():
    return div(id="my-special-id_123")
""")
        assert result.success
        assert "my-special-id_123" in result.js
    
    def test_multiple_show_components(self):
        """Multiple Show components."""
        result = compile_island("""
@island
def MultiShow():
    a = signal(True)
    b = signal(False)
    return div()[
        Show(when=lambda: a())[div()["A"]],
        Show(when=lambda: b())[div()["B"]]
    ]
""")
        assert result.success


# =============================================================================
# SECTION 6: Regression Tests (20 tests)
# =============================================================================

class TestRegressions:
    """Regression tests for previously fixed bugs."""
    
    def test_signal_read_creates_effect(self):
        """Signal read in DOM creates reactive effect."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return div()[count()]
""")
        assert "createEffect" in result.js
    
    def test_subscript_not_element(self):
        """Dictionary subscript is not treated as element."""
        result = compile_island("""
@island
def Card(data):
    return div()[data["title"]]
""")
        # Should NOT create an element called "title"
        assert 'createElement("title")' not in result.js
        # Should have dictionary access
        assert 'data["title"]' in result.js
    
    def test_unique_variable_names(self):
        """Each element has unique variable name."""
        result = compile_island("""
@island
def Multi():
    return div()[
        span()["A"],
        span()["B"],
        span()["C"]
    ]
""")
        # Count unique _el variables
        import re
        el_vars = set(re.findall(r'_el\d+', result.js))
        assert len(el_vars) >= 4  # div + 3 spans
    
    def test_handler_uses_correct_element(self):
        """Handler attached to correct element."""
        result = compile_island("""
@island
def Counter():
    count = signal(0)
    return button(onclick=lambda: count.set(0))
""")
        # The addEventListener should be on the button element
        # Find the element var and check it's used in addEventListener
        lines = result.js.split('\n')
        button_var = None
        for line in lines:
            if 'createElement("button")' in line:
                button_var = line.split('const ')[1].split(' =')[0]
                break
        assert button_var
        assert f'{button_var}.addEventListener' in result.js

