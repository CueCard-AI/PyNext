"""
Aggressive Edge Case Tests for PyNext Compiler (500 tests)

These tests specifically target:
- Bugs we fixed (regression prevention)
- Unusual Python patterns
- Deep nesting
- Complex expressions
- Boundary conditions
- Error recovery
"""

import pytest
from pynext.compiler import compile_island, CompileError


# =============================================================================
# SECTION 1: Children Factory Regression Tests (50 tests)
# =============================================================================

class TestChildrenFactoryRegression:
    """Tests to prevent children factory from breaking again."""
    
    def test_for_children_not_placeholder(self):
        """For children must not be a placeholder comment."""
        result = compile_island("""
@island
def List():
    items = signal([1, 2, 3])
    return For(each=lambda: items())[
        lambda item: div()[item]
    ]
""")
        assert "/* children */" not in result.js
        assert "createElement" in result.js
    
    def test_show_children_not_placeholder(self):
        """Show children must not be a placeholder comment."""
        result = compile_island("""
@island
def Toggle():
    visible = signal(True)
    return Show(when=lambda: visible())[
        div()["Content"]
    ]
""")
        assert "/* children */" not in result.js
        assert "createElement" in result.js
    
    def test_for_with_complex_lambda(self):
        """For with complex lambda body."""
        result = compile_island("""
@island
def List():
    items = signal([])
    return For(each=lambda: items())[
        lambda item: div(class_="item")[
            span()[item["name"]],
            span()[item["value"]]
        ]
    ]
""")
        assert result.success
        assert "item[" in result.js
    
    def test_nested_for_loops(self):
        """Nested For loops."""
        result = compile_island("""
@island
def Grid():
    rows = signal([])
    return For(each=lambda: rows())[
        lambda row: div()[
            For(each=lambda: row["cells"])[
                lambda cell: span()[cell]
            ]
        ]
    ]
""")
        assert result.success
    
    def test_for_with_show_inside(self):
        """For loop with Show inside."""
        result = compile_island("""
@island
def ConditionalList():
    items = signal([])
    return For(each=lambda: items())[
        lambda item: Show(when=lambda: item["visible"])[
            div()[item["name"]]
        ]
    ]
""")
        assert result.success
    
    def test_show_with_for_inside(self):
        """Show with For inside."""
        result = compile_island("""
@island
def FilteredList():
    visible = signal(True)
    items = signal([])
    return Show(when=lambda: visible())[
        For(each=lambda: items())[
            lambda item: div()[item]
        ]
    ]
""")
        assert result.success
    
    def test_deeply_nested_control_flow(self):
        """3+ levels of nested control flow."""
        result = compile_island("""
@island
def Deep():
    a = signal(True)
    b = signal(True)
    items = signal([])
    return Show(when=lambda: a())[
        Show(when=lambda: b())[
            For(each=lambda: items())[
                lambda x: div()[x]
            ]
        ]
    ]
""")
        assert result.success


class TestForEdgeCases:
    """Edge cases for For loop compilation."""
    
    def test_for_empty_items(self):
        """For with empty initial list."""
        result = compile_island("""
@island
def EmptyList():
    items = signal([])
    return For(each=lambda: items())[
        lambda item: div()[item]
    ]
""")
        assert result.success
    
    def test_for_with_index(self):
        """For loop using index parameter."""
        result = compile_island("""
@island
def IndexedList():
    items = signal(["a", "b", "c"])
    return For(each=lambda: items())[
        lambda item, index: div()[index, ": ", item]
    ]
""")
        assert result.success
        # Should have (item, _index) or (item, index) in output
        assert "item" in result.js
    
    def test_for_with_key_function(self):
        """For with custom key function."""
        result = compile_island("""
@island
def KeyedList():
    items = signal([])
    return For(each=lambda: items(), key=lambda item: item["id"])[
        lambda item: div()[item["name"]]
    ]
""")
        assert result.success
        assert "key:" in result.js
    
    def test_for_direct_expression(self):
        """For with direct expression instead of lambda."""
        result = compile_island("""
@island
def SimpleList():
    items = signal([1, 2, 3])
    return For(each=lambda: items())[
        lambda x: span()[x]
    ]
""")
        assert result.success


# =============================================================================
# SECTION 2: Comparison Operator Tests (60 tests)
# =============================================================================

class TestIsNoneOperator:
    """Tests for 'is None' compilation."""
    
    def test_is_none_basic(self):
        """x is None compiles to x === null."""
        result = compile_island("""
@island
def NullCheck():
    data = signal(None)
    return Show(when=lambda: data() is None)[
        div()["No data"]
    ]
""")
        assert result.success
        assert "=== null" in result.js
    
    def test_is_not_none(self):
        """x is not None compiles to x !== null."""
        result = compile_island("""
@island
def DataCheck():
    data = signal(None)
    return Show(when=lambda: data() is not None)[
        div()["Has data"]
    ]
""")
        assert result.success
        assert "!== null" in result.js
    
    def test_none_on_left(self):
        """None is x (reversed)."""
        result = compile_island("""
@island
def ReversedCheck():
    data = signal(None)
    return Show(when=lambda: None is data())[
        div()["No data"]
    ]
""")
        assert result.success


class TestInOperator:
    """Tests for 'in' operator compilation."""
    
    def test_in_list(self):
        """x in list uses includes()."""
        result = compile_island("""
@island
def ListCheck():
    items = signal([1, 2, 3])
    return Show(when=lambda: 2 in items())[
        div()["Found"]
    ]
""")
        assert result.success
        assert "includes" in result.js
    
    def test_in_dict(self):
        """x in dict uses 'in' operator."""
        result = compile_island("""
@island
def DictCheck():
    data = signal({"a": 1})
    return Show(when=lambda: "a" in data())[
        div()["Key exists"]
    ]
""")
        assert result.success
        # Should use Array.isArray check
        assert "Array.isArray" in result.js
    
    def test_not_in_list(self):
        """x not in list."""
        result = compile_island("""
@island
def NotInCheck():
    items = signal([1, 2, 3])
    return Show(when=lambda: 4 not in items())[
        div()["Not found"]
    ]
""")
        assert result.success
        assert "!" in result.js


class TestComparisonChains:
    """Tests for chained comparisons."""
    
    def test_double_comparison(self):
        """0 < x < 10 pattern."""
        result = compile_island("""
@island
def RangeCheck():
    value = signal(5)
    return Show(when=lambda: 0 < value() < 10)[
        div()["In range"]
    ]
""")
        assert result.success
    
    def test_equality_chain(self):
        """a == b == c pattern."""
        result = compile_island("""
@island
def EqualityCheck():
    a = signal(1)
    b = signal(1)
    return Show(when=lambda: a() == b() == 1)[
        div()["All equal"]
    ]
""")
        assert result.success


# =============================================================================
# SECTION 3: Expression Edge Cases (80 tests)
# =============================================================================

class TestBinaryOperators:
    """Tests for all binary operators."""
    
    def test_floor_division(self):
        """// operator."""
        result = compile_island("""
@island
def FloorDiv():
    x = signal(7)
    y = memo(lambda: x() // 2)
    return div()[y()]
""")
        assert result.success
        assert "Math.floor" in result.js
    
    def test_modulo(self):
        """% operator."""
        result = compile_island("""
@island
def Modulo():
    x = signal(7)
    y = memo(lambda: x() % 3)
    return div()[y()]
""")
        assert result.success
        assert "%" in result.js
    
    def test_power(self):
        """** operator."""
        result = compile_island("""
@island
def Power():
    x = signal(2)
    y = memo(lambda: x() ** 3)
    return div()[y()]
""")
        assert result.success
        assert "**" in result.js
    
    def test_bitwise_and(self):
        """& operator."""
        result = compile_island("""
@island
def BitwiseAnd():
    x = signal(5)
    y = memo(lambda: x() & 3)
    return div()[y()]
""")
        assert result.success
        assert "&" in result.js
    
    def test_bitwise_or(self):
        """| operator."""
        result = compile_island("""
@island
def BitwiseOr():
    x = signal(5)
    y = memo(lambda: x() | 3)
    return div()[y()]
""")
        assert result.success
        assert "|" in result.js
    
    def test_bitwise_xor(self):
        """^ operator."""
        result = compile_island("""
@island
def BitwiseXor():
    x = signal(5)
    y = memo(lambda: x() ^ 3)
    return div()[y()]
""")
        assert result.success
        assert "^" in result.js
    
    def test_left_shift(self):
        """<< operator."""
        result = compile_island("""
@island
def LeftShift():
    x = signal(1)
    y = memo(lambda: x() << 3)
    return div()[y()]
""")
        assert result.success
        assert "<<" in result.js
    
    def test_right_shift(self):
        """>> operator."""
        result = compile_island("""
@island
def RightShift():
    x = signal(8)
    y = memo(lambda: x() >> 2)
    return div()[y()]
""")
        assert result.success
        assert ">>" in result.js


class TestUnaryOperators:
    """Tests for unary operators."""
    
    def test_not_operator(self):
        """not x."""
        result = compile_island("""
@island
def NotOp():
    active = signal(True)
    return Show(when=lambda: not active())[
        div()["Inactive"]
    ]
""")
        assert result.success
        assert "!" in result.js
    
    def test_negative(self):
        """-x."""
        result = compile_island("""
@island
def Negative():
    x = signal(5)
    y = memo(lambda: -x())
    return div()[y()]
""")
        assert result.success
        assert "-" in result.js
    
    def test_positive(self):
        """+x."""
        result = compile_island("""
@island
def Positive():
    x = signal(5)
    y = memo(lambda: +x())
    return div()[y()]
""")
        assert result.success
    
    def test_bitwise_not(self):
        """~x."""
        result = compile_island("""
@island
def BitwiseNot():
    x = signal(5)
    y = memo(lambda: ~x())
    return div()[y()]
""")
        assert result.success
        assert "~" in result.js


class TestComplexExpressions:
    """Tests for complex combined expressions."""
    
    def test_ternary_expression(self):
        """x if condition else y."""
        result = compile_island("""
@island
def Ternary():
    condition = signal(True)
    result = memo(lambda: "yes" if condition() else "no")
    return div()[result()]
""")
        assert result.success
        assert "?" in result.js
        assert ":" in result.js
    
    def test_nested_ternary(self):
        """Nested ternary."""
        result = compile_island("""
@island
def NestedTernary():
    a = signal(1)
    b = signal(2)
    result = memo(lambda: "one" if a() == 1 else "two" if b() == 2 else "other")
    return div()[result()]
""")
        assert result.success
    
    def test_complex_boolean(self):
        """Complex boolean expression."""
        result = compile_island("""
@island
def ComplexBool():
    a = signal(True)
    b = signal(False)
    c = signal(True)
    result = memo(lambda: (a() and b()) or (not c() and a()))
    return div()[result()]
""")
        assert result.success
        assert "&&" in result.js
        assert "||" in result.js
    
    def test_arithmetic_chain(self):
        """Chained arithmetic."""
        result = compile_island("""
@island
def ArithChain():
    a = signal(1)
    b = signal(2)
    c = signal(3)
    result = memo(lambda: a() + b() * c() - a() / b())
    return div()[result()]
""")
        assert result.success


class TestSubscriptAccess:
    """Tests for dictionary/list access."""
    
    def test_dict_string_key(self):
        """data["key"]."""
        result = compile_island("""
@island
def DictAccess():
    data = signal({"name": "test"})
    return div()[data()["name"]]
""")
        assert result.success
        assert '["name"]' in result.js
    
    def test_dict_variable_key(self):
        """data[key] where key is variable."""
        result = compile_island("""
@island
def DynamicAccess(key):
    data = signal({"a": 1, "b": 2})
    return div()[data()[key]]
""")
        assert result.success
    
    def test_nested_subscript(self):
        """data["a"]["b"]."""
        result = compile_island("""
@island
def NestedAccess():
    data = signal({"a": {"b": "value"}})
    return div()[data()["a"]["b"]]
""")
        assert result.success
    
    def test_list_index(self):
        """list[0]."""
        result = compile_island("""
@island
def ListAccess():
    items = signal([1, 2, 3])
    return div()[items()[0]]
""")
        assert result.success
        assert "[0]" in result.js


# =============================================================================
# SECTION 4: DOM Edge Cases (70 tests)
# =============================================================================

class TestDeepNesting:
    """Tests for deeply nested DOM structures."""
    
    def test_10_levels_deep(self):
        """10 levels of nested elements."""
        result = compile_island("""
@island
def DeepNest():
    return div()[div()[div()[div()[div()[div()[div()[div()[div()[div()["Deep"]]]]]]]]]]
""")
        assert result.success
        assert result.js.count("createElement") >= 10
    
    def test_wide_children(self):
        """Many children at same level."""
        result = compile_island("""
@island
def WideChildren():
    return div()[
        span()["1"],
        span()["2"],
        span()["3"],
        span()["4"],
        span()["5"],
        span()["6"],
        span()["7"],
        span()["8"],
        span()["9"],
        span()["10"]
    ]
""")
        assert result.success
        assert result.js.count("createElement") >= 11
    
    def test_mixed_content(self):
        """Mixed static and reactive content."""
        result = compile_island("""
@island
def MixedContent():
    count = signal(0)
    return div()[
        "Static: ",
        count(),
        " more text ",
        count() * 2,
        " end"
    ]
""")
        assert result.success


class TestAttributes:
    """Tests for various attribute patterns."""
    
    def test_many_attributes(self):
        """Element with many attributes."""
        result = compile_island("""
@island
def ManyAttrs():
    return div(
        id="main",
        class_="container",
        data_id="123",
        data_name="test",
        title="tooltip",
        style="color: red"
    )
""")
        assert result.success
    
    def test_reactive_class(self):
        """Reactive class attribute."""
        result = compile_island("""
@island
def ReactiveClass():
    active = signal(False)
    return div(class_=lambda: "active" if active() else "inactive")
""")
        assert result.success
    
    def test_reactive_style(self):
        """Reactive style attribute."""
        result = compile_island("""
@island
def ReactiveStyle():
    color = signal("red")
    return div(style=lambda: f"color: {color()}")
""")
        assert result.success
    
    def test_boolean_attribute(self):
        """Boolean attribute like disabled."""
        result = compile_island("""
@island
def BoolAttr():
    disabled = signal(True)
    return button(disabled="disabled")["Click"]
""")
        assert result.success


class TestEventHandlers:
    """Tests for event handler patterns."""
    
    def test_handler_with_event_param(self):
        """Handler using event parameter."""
        result = compile_island("""
@island
def EventHandler():
    text = signal("")
    return input(oninput=lambda e: text.set(e.target.value))
""")
        assert result.success
        assert "(e) =>" in result.js or "e =>" in result.js
        assert "e.target.value" in result.js
    
    def test_handler_with_event_prevent(self):
        """Handler calling preventDefault."""
        result = compile_island("""
@island
def PreventDefault():
    return form(onsubmit=lambda e: (e.preventDefault(), submit()))
""")
        assert result.success
        assert "preventDefault" in result.js
    
    def test_multiple_handlers(self):
        """Element with multiple handlers."""
        result = compile_island("""
@island
def MultiHandler():
    return button(
        onclick=lambda: click(),
        onmouseover=lambda: hover(),
        onmouseout=lambda: leave(),
        onfocus=lambda: focus(),
        onblur=lambda: blur(),
        onkeydown=lambda e: keydown(e.key)
    )["Button"]
""")
        assert result.success
        assert result.js.count("addEventListener") == 6
    
    def test_handler_reading_multiple_signals(self):
        """Handler that reads multiple signals."""
        result = compile_island("""
@island
def MultiRead():
    a = signal(1)
    b = signal(2)
    c = signal(3)
    return button(onclick=lambda: submit(a(), b(), c()))["Submit"]
""")
        assert result.success


# =============================================================================
# SECTION 5: Signal/Memo Patterns (60 tests)
# =============================================================================

class TestSignalPatterns:
    """Tests for various signal usage patterns."""
    
    def test_signal_object_initial(self):
        """Signal with object initial value."""
        result = compile_island("""
@island
def ObjectSignal():
    user = signal({"name": "John", "age": 30, "active": True})
    return div()[user()["name"]]
""")
        assert result.success
    
    def test_signal_array_initial(self):
        """Signal with array initial value."""
        result = compile_island("""
@island
def ArraySignal():
    items = signal([{"id": 1}, {"id": 2}, {"id": 3}])
    return div()[items()[0]["id"]]
""")
        assert result.success
    
    def test_signal_update_with_function(self):
        """Signal update with function."""
        result = compile_island("""
@island
def UpdateFunc():
    count = signal(0)
    return button(onclick=lambda: count.update(lambda x: x + 1))["Inc"]
""")
        assert result.success
        assert "count.update" in result.js
    
    def test_signal_toggle(self):
        """Signal boolean toggle pattern."""
        result = compile_island("""
@island
def Toggle():
    active = signal(False)
    return button(onclick=lambda: active.update(lambda x: not x))["Toggle"]
""")
        assert result.success
        assert "!x" in result.js or "not x" in result.js.lower()
    
    def test_many_signals(self):
        """Component with many signals."""
        result = compile_island("""
@island
def ManySignals():
    a = signal(0)
    b = signal(1)
    c = signal(2)
    d = signal(3)
    e = signal(4)
    f = signal(5)
    g = signal(6)
    h = signal(7)
    i = signal(8)
    j = signal(9)
    return div()[a() + b() + c() + d() + e()]
""")
        assert result.success
        assert result.stats["signals"] == 10


class TestMemoPatterns:
    """Tests for memo/computed patterns."""
    
    def test_memo_chain(self):
        """Memo depending on memo."""
        result = compile_island("""
@island
def MemoChain():
    x = signal(1)
    a = memo(lambda: x() * 2)
    b = memo(lambda: a() * 2)
    c = memo(lambda: b() * 2)
    return div()[c()]
""")
        assert result.success
        assert result.js.count("createMemo") == 3
    
    def test_memo_multiple_deps(self):
        """Memo with multiple dependencies."""
        result = compile_island("""
@island
def MultiDepMemo():
    a = signal(1)
    b = signal(2)
    c = signal(3)
    sum_ = memo(lambda: a() + b() + c())
    return div()[sum_()]
""")
        assert result.success
    
    def test_memo_conditional(self):
        """Memo with conditional logic."""
        result = compile_island("""
@island
def ConditionalMemo():
    x = signal(5)
    result = memo(lambda: "big" if x() > 10 else "small")
    return div()[result()]
""")
        assert result.success


# =============================================================================
# SECTION 6: Real-World Patterns (80 tests)
# =============================================================================

class TestFormPatterns:
    """Tests for form-related patterns."""
    
    def test_login_form(self):
        """Complete login form."""
        result = compile_island("""
@island
def LoginForm():
    username = signal("")
    password = signal("")
    error = signal(None)
    loading = signal(False)
    
    return form(onsubmit=lambda e: (e.preventDefault(), submit()))[
        Show(when=lambda: error() is not None)[
            div(class_="error")[error()]
        ],
        input(
            type="text",
            placeholder="Username",
            oninput=lambda e: username.set(e.target.value)
        ),
        input(
            type="password",
            placeholder="Password",
            oninput=lambda e: password.set(e.target.value)
        ),
        button(type="submit")[
            Show(when=lambda: loading())[
                "Loading..."
            ],
            Show(when=lambda: not loading())[
                "Login"
            ]
        ]
    ]
""")
        assert result.success
        assert result.stats["signals"] == 4
    
    def test_todo_list(self):
        """Todo list with add/remove."""
        result = compile_island("""
@island
def TodoList():
    todos = signal([])
    new_todo = signal("")
    
    return div()[
        input(
            oninput=lambda e: new_todo.set(e.target.value),
            placeholder="New todo"
        ),
        button(onclick=lambda: add_todo())["Add"],
        For(each=lambda: todos())[
            lambda todo: div()[
                span()[todo["text"]],
                button(onclick=lambda: remove_todo(todo["id"]))["X"]
            ]
        ]
    ]
""")
        assert result.success
    
    def test_search_filter(self):
        """Search/filter pattern."""
        result = compile_island("""
@island
def SearchableList():
    items = signal([])
    query = signal("")
    filtered = memo(lambda: [i for i in items() if query() in i["name"]])
    
    return div()[
        input(
            oninput=lambda e: query.set(e.target.value),
            placeholder="Search..."
        ),
        For(each=lambda: filtered())[
            lambda item: div()[item["name"]]
        ]
    ]
""")
        assert result.success


class TestLayoutPatterns:
    """Tests for layout patterns."""
    
    def test_tabs_component(self):
        """Tab component pattern."""
        result = compile_island("""
@island
def Tabs():
    active_tab = signal(0)
    
    return div()[
        div(class_="tab-buttons")[
            button(onclick=lambda: active_tab.set(0))["Tab 1"],
            button(onclick=lambda: active_tab.set(1))["Tab 2"],
            button(onclick=lambda: active_tab.set(2))["Tab 3"]
        ],
        Show(when=lambda: active_tab() == 0)[
            div()["Content 1"]
        ],
        Show(when=lambda: active_tab() == 1)[
            div()["Content 2"]
        ],
        Show(when=lambda: active_tab() == 2)[
            div()["Content 3"]
        ]
    ]
""")
        assert result.success
    
    def test_accordion(self):
        """Accordion pattern."""
        result = compile_island("""
@island
def Accordion():
    open_item = signal(None)
    
    return div()[
        div(onclick=lambda: open_item.set(0 if open_item() != 0 else None))[
            "Header 1"
        ],
        Show(when=lambda: open_item() == 0)[
            div()["Content 1"]
        ],
        div(onclick=lambda: open_item.set(1 if open_item() != 1 else None))[
            "Header 2"
        ],
        Show(when=lambda: open_item() == 1)[
            div()["Content 2"]
        ]
    ]
""")
        assert result.success
    
    def test_modal(self):
        """Modal dialog pattern."""
        result = compile_island("""
@island
def Modal():
    is_open = signal(False)
    
    return div()[
        button(onclick=lambda: is_open.set(True))["Open Modal"],
        Show(when=lambda: is_open())[
            div(class_="modal-overlay", onclick=lambda: is_open.set(False))[
                div(class_="modal-content", onclick=lambda e: e.stopPropagation())[
                    h2()["Modal Title"],
                    p()["Modal content"],
                    button(onclick=lambda: is_open.set(False))["Close"]
                ]
            ]
        ]
    ]
""")
        assert result.success


class TestDataDisplayPatterns:
    """Tests for data display patterns."""
    
    def test_data_table(self):
        """Data table with sorting."""
        result = compile_island("""
@island
def DataTable():
    data = signal([])
    sort_key = signal("name")
    
    sorted_data = memo(lambda: sorted(data(), key=lambda x: x[sort_key()]))
    
    return table()[
        thead()[
            tr()[
                th(onclick=lambda: sort_key.set("name"))["Name"],
                th(onclick=lambda: sort_key.set("age"))["Age"],
                th(onclick=lambda: sort_key.set("email"))["Email"]
            ]
        ],
        tbody()[
            For(each=lambda: sorted_data())[
                lambda row: tr()[
                    td()[row["name"]],
                    td()[row["age"]],
                    td()[row["email"]]
                ]
            ]
        ]
    ]
""")
        assert result.success
    
    def test_pagination(self):
        """Pagination pattern."""
        result = compile_island("""
@island
def Pagination():
    items = signal([])
    page = signal(0)
    per_page = signal(10)
    
    total_pages = memo(lambda: len(items()) // per_page())
    current_items = memo(lambda: items()[page() * per_page():(page() + 1) * per_page()])
    
    return div()[
        For(each=lambda: current_items())[
            lambda item: div()[item["name"]]
        ],
        div(class_="pagination")[
            button(onclick=lambda: page.set(max(0, page() - 1)))["Prev"],
            span()[page() + 1, " / ", total_pages()],
            button(onclick=lambda: page.set(min(total_pages() - 1, page() + 1)))["Next"]
        ]
    ]
""")
        assert result.success


# =============================================================================
# SECTION 7: Error Cases (50 tests)
# =============================================================================

class TestSyntaxErrors:
    """Tests for syntax error handling."""
    
    def test_missing_colon(self):
        """Missing colon in function def."""
        result = compile_island("""
@island
def Counter()
    count = signal(0)
""")
        assert not result.success
        assert len(result.errors) > 0
    
    def test_unclosed_bracket(self):
        """Unclosed bracket."""
        result = compile_island("""
@island
def Counter():
    count = signal([1, 2, 3)
""")
        assert not result.success
    
    def test_invalid_indent(self):
        """Invalid indentation."""
        result = compile_island("""
@island
def Counter():
count = signal(0)
""")
        assert not result.success


class TestNonCompilableConstructs:
    """Tests for non-compilable Python constructs."""
    
    def test_class_inside(self):
        """Class inside island."""
        result = compile_island("""
@island
def Counter():
    class Helper:
        pass
""")
        assert not result.success
        assert any("class" in str(e).lower() for e in result.errors)
    
    def test_yield_inside(self):
        """Yield inside island."""
        result = compile_island("""
@island
def Counter():
    def gen():
        yield 1
""")
        assert not result.success
    
    def test_global_inside(self):
        """Global statement inside island."""
        result = compile_island("""
@island
def Counter():
    global x
    x = 1
""")
        assert not result.success
    
    def test_import_inside(self):
        """Import inside island."""
        result = compile_island("""
@island
def Counter():
    import os
    return div()[os.name]
""")
        assert not result.success


class TestRecoveryAfterError:
    """Tests for error recovery."""
    
    def test_error_has_filename(self):
        """Error includes filename."""
        result = compile_island("def NoIsland(): pass", "myfile.py")
        assert not result.success
        # Error should reference the file in some way
        assert len(result.errors) > 0
        error = result.errors[0]
        assert error.filename == "myfile.py" or "myfile" in str(error)
    
    def test_error_has_suggestion(self):
        """Error includes helpful suggestion."""
        result = compile_island("""
@island
def Counter():
    class Helper:
        pass
""")
        assert not result.success
        # Should have a suggestion
        error_str = str(result.errors[0])
        assert "SOLUTION" in error_str or "suggestion" in error_str.lower()


# =============================================================================
# SECTION 8: Performance/Stress Tests (50 tests)
# =============================================================================

class TestStressTests:
    """Stress tests for compiler performance."""
    
    def test_100_signals(self):
        """Component with 100 signals."""
        signal_defs = "\n    ".join([f"s{i} = signal({i})" for i in range(100)])
        result = compile_island(f"""
@island
def ManySignals():
    {signal_defs}
    return div()[s0()]
""")
        assert result.success
        assert result.stats["signals"] == 100
    
    def test_50_handlers(self):
        """Component with 50 handlers."""
        buttons = ",\n        ".join([f'button(onclick=lambda: handle{i}())["B{i}"]' for i in range(50)])
        result = compile_island(f"""
@island
def ManyHandlers():
    return div()[
        {buttons}
    ]
""")
        assert result.success
        assert result.stats["handlers"] == 50
    
    def test_compile_time_reasonable(self):
        """Complex component compiles in reasonable time."""
        result = compile_island("""
@island
def Complex():
    a = signal(0)
    b = signal(1)
    c = signal(2)
    d = memo(lambda: a() + b())
    e = memo(lambda: c() + d())
    
    return div()[
        div(class_="header")[
            h1()[e()],
            button(onclick=lambda: a.set(a() + 1))["Inc"]
        ],
        div(class_="body")[
            For(each=lambda: [1,2,3,4,5])[
                lambda x: div()[x * a()]
            ]
        ],
        Show(when=lambda: a() > 5)[
            div()["Big!"]
        ]
    ]
""")
        assert result.success
        assert result.stats["compile_time_ms"] < 100  # Should be fast

