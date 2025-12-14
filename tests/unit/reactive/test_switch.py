"""
Tests for Switch/Match Components - Multi-Branch Conditionals

50 comprehensive tests covering:
- Basic rendering (15 tests)
- Reactive updates (20 tests)
- Edge cases (15 tests)
"""

import pytest
from pynext.reactive.control_flow import Switch, Match
from pynext.reactive.signal import Signal
from pynext.reactive.store import Store


# =============================================================================
# SECTION 1: BASIC RENDERING (15 tests)
# =============================================================================

class TestSwitchBasicRendering:
    """Basic Switch/Match rendering tests."""
    
    def test_switch_single_match(self):
        """Switch renders single matching branch."""
        switch = Switch()[
            Match(when=True)["First"]
        ]
        html = switch.render()
        
        assert "First" in html
        assert 'data-match="0"' in html
    
    def test_switch_first_true_match(self):
        """Switch renders first true match only."""
        switch = Switch()[
            Match(when=True)["First"],
            Match(when=True)["Second"]
        ]
        html = switch.render()
        
        assert "First" in html
        assert "Second" not in html
    
    def test_switch_skips_false_matches(self):
        """Switch skips false matches."""
        switch = Switch()[
            Match(when=False)["First"],
            Match(when=True)["Second"],
            Match(when=True)["Third"]
        ]
        html = switch.render()
        
        assert "Second" in html
        assert "First" not in html
        assert "Third" not in html
    
    def test_switch_no_match(self):
        """Switch renders empty when no match."""
        switch = Switch()[
            Match(when=False)["First"],
            Match(when=False)["Second"]
        ]
        html = switch.render()
        
        assert "First" not in html
        assert "Second" not in html
        assert 'data-match="-1"' in html
    
    def test_switch_default_match(self):
        """Switch with default (always true) match."""
        switch = Switch()[
            Match(when=False)["First"],
            Match(when=True)["Default"]  # Acts as else
        ]
        html = switch.render()
        
        assert "Default" in html
    
    def test_switch_callable_condition(self):
        """Switch with callable conditions."""
        switch = Switch()[
            Match(when=lambda: False)["First"],
            Match(when=lambda: True)["Second"]
        ]
        html = switch.render()
        
        assert "Second" in html
    
    def test_switch_unique_id(self):
        """Each Switch has unique ID."""
        s1 = Switch()[Match(when=True)["A"]]
        s2 = Switch()[Match(when=True)["B"]]
        
        assert s1._id != s2._id
    
    def test_switch_data_attribute(self):
        """Switch includes data-switch attribute."""
        switch = Switch()[Match(when=True)["Content"]]
        html = switch.render()
        
        assert 'data-switch=' in html
    
    def test_switch_str_method(self):
        """Switch __str__ returns rendered HTML."""
        switch = Switch()[Match(when=True)["Content"]]
        assert str(switch) == switch.render()
    
    def test_switch_repr(self):
        """Switch __repr__ is informative."""
        switch = Switch()[
            Match(when=True)["A"],
            Match(when=True)["B"]
        ]
        assert "Switch" in repr(switch)
        assert "2" in repr(switch)
    
    def test_match_str_method(self):
        """Match __str__ returns rendered HTML."""
        match = Match(when=True)["Content"]
        assert str(match) == match.render()
    
    def test_match_repr(self):
        """Match __repr__ is informative."""
        match = Match(when=True)["Content"]
        assert "Match" in repr(match)
    
    def test_switch_empty_matches_list(self):
        """Switch handles empty matches list."""
        switch = Switch()
        html = switch.render()
        
        assert 'data-match="-1"' in html
    
    def test_switch_single_match_false(self):
        """Switch with single false match."""
        switch = Switch()[
            Match(when=False)["Never"]
        ]
        html = switch.render()
        
        assert "Never" not in html
    
    def test_switch_html_content(self):
        """Switch renders HTML content."""
        switch = Switch()[
            Match(when=True)["<div class='active'>Content</div>"]
        ]
        html = switch.render()
        
        assert "class='active'" in html


# =============================================================================
# SECTION 2: REACTIVE UPDATES (20 tests)
# =============================================================================

class TestSwitchReactiveUpdates:
    """Tests for Switch with reactive signals and stores."""
    
    def test_switch_signal_condition(self):
        """Switch with Signal condition."""
        active = Signal(True)
        switch = Switch()[
            Match(when=lambda: active())["Active"],
            Match(when=True)["Inactive"]
        ]
        
        html = switch.render()
        assert "Active" in html
    
    def test_switch_signal_changes(self):
        """Switch updates when signal changes."""
        status = Signal("loading")
        switch = Switch()[
            Match(when=lambda: status() == "loading")["Loading..."],
            Match(when=lambda: status() == "success")["Success!"],
            Match(when=lambda: status() == "error")["Error!"]
        ]
        
        assert "Loading" in switch.render()
        
        status.set("success")
        assert "Success" in switch.render()
        
        status.set("error")
        assert "Error" in switch.render()
    
    def test_switch_store_condition(self):
        """Switch with Store property condition."""
        state = Store({"view": "home"})
        switch = Switch()[
            Match(when=lambda: state.view == "home")["Home"],
            Match(when=lambda: state.view == "profile")["Profile"],
            Match(when=True)["404"]
        ]
        
        assert "Home" in switch.render()
        
        state.view = "profile"
        assert "Profile" in switch.render()
    
    def test_switch_numeric_condition(self):
        """Switch with numeric signal condition."""
        count = Signal(0)
        switch = Switch()[
            Match(when=lambda: count() < 0)["Negative"],
            Match(when=lambda: count() == 0)["Zero"],
            Match(when=lambda: count() > 0)["Positive"]
        ]
        
        assert "Zero" in switch.render()
        
        count.set(5)
        assert "Positive" in switch.render()
        
        count.set(-3)
        assert "Negative" in switch.render()
    
    def test_switch_complex_condition(self):
        """Switch with complex signal condition."""
        user = Store({"role": "guest", "premium": False})
        switch = Switch()[
            Match(when=lambda: user.role == "admin")["Admin Panel"],
            Match(when=lambda: user.role == "user" and user.premium)["Premium"],
            Match(when=lambda: user.role == "user")["Basic"],
            Match(when=True)["Guest"]
        ]
        
        assert "Guest" in switch.render()
        
        user.role = "user"
        assert "Basic" in switch.render()
        
        user.premium = True
        assert "Premium" in switch.render()
    
    def test_switch_content_reads_signal(self):
        """Switch content can read signals."""
        name = Signal("Alice")
        switch = Switch()[
            Match(when=True)[lambda: f"Hello, {name()}!"]
        ]
        
        assert "Hello, Alice!" in switch.render()
        
        name.set("Bob")
        assert "Hello, Bob!" in switch.render()
    
    def test_switch_multiple_signals(self):
        """Switch with multiple signal conditions."""
        a = Signal(False)
        b = Signal(False)
        switch = Switch()[
            Match(when=lambda: a() and b())["Both"],
            Match(when=lambda: a())["A only"],
            Match(when=lambda: b())["B only"],
            Match(when=True)["Neither"]
        ]
        
        assert "Neither" in switch.render()
        
        a.set(True)
        assert "A only" in switch.render()
        
        b.set(True)
        assert "Both" in switch.render()
    
    def test_switch_enum_like_pattern(self):
        """Switch with enum-like pattern."""
        mode = Signal("view")
        switch = Switch()[
            Match(when=lambda: mode() == "view")["ViewMode"],
            Match(when=lambda: mode() == "edit")["EditMode"],
            Match(when=lambda: mode() == "create")["CreateMode"]
        ]
        
        assert "ViewMode" in switch.render()
        
        mode.set("edit")
        assert "EditMode" in switch.render()
    
    def test_switch_derived_condition(self):
        """Switch with derived condition."""
        from pynext.reactive.memo import Memo
        
        items = Signal([1, 2, 3])
        has_items = Memo(lambda: len(items()) > 0)
        
        switch = Switch()[
            Match(when=lambda: has_items())["Has items"],
            Match(when=True)["No items"]
        ]
        
        assert "Has items" in switch.render()
        
        items.set([])
        assert "No items" in switch.render()
    
    def test_switch_cascading_conditions(self):
        """Switch with cascading conditions."""
        score = Signal(75)
        switch = Switch()[
            Match(when=lambda: score() >= 90)["A"],
            Match(when=lambda: score() >= 80)["B"],
            Match(when=lambda: score() >= 70)["C"],
            Match(when=lambda: score() >= 60)["D"],
            Match(when=True)["F"]
        ]
        
        assert "C" in switch.render()
        
        score.set(95)
        assert "A" in switch.render()
        
        score.set(55)
        assert "F" in switch.render()
    
    def test_switch_rapid_changes(self):
        """Switch handles rapid condition changes."""
        status = Signal("a")
        switch = Switch()[
            Match(when=lambda: status() == "a")["A"],
            Match(when=lambda: status() == "b")["B"],
            Match(when=lambda: status() == "c")["C"]
        ]
        
        for _ in range(50):
            status.set("a")
            assert "A" in switch.render()
            status.set("b")
            assert "B" in switch.render()
            status.set("c")
            assert "C" in switch.render()
    
    def test_switch_with_effect(self):
        """Switch works alongside Effect."""
        from pynext.reactive.effect import Effect
        
        active = Signal("x")
        renders = [0]
        
        @Effect
        def track():
            active()
            renders[0] += 1
        
        switch = Switch()[
            Match(when=lambda: active() == "x")["X"],
            Match(when=True)["Other"]
        ]
        
        switch.render()
        assert renders[0] >= 1
    
    def test_switch_batch_updates(self):
        """Switch handles batched updates."""
        from pynext.reactive.batch import batch
        
        a = Signal("1")
        b = Signal("2")
        switch = Switch()[
            Match(when=lambda: a() == "1" and b() == "1")["Both 1"],
            Match(when=True)["Other"]
        ]
        
        assert "Other" in switch.render()
        
        batch(lambda: (a.set("1"), b.set("1")))
        assert "Both 1" in switch.render()
    
    def test_switch_nested_reactive(self):
        """Switch with nested reactive content."""
        mode = Signal("a")
        value = Signal(10)
        
        switch = Switch()[
            Match(when=lambda: mode() == "a")[lambda: f"A: {value()}"],
            Match(when=lambda: mode() == "b")[lambda: f"B: {value() * 2}"]
        ]
        
        assert "A: 10" in switch.render()
        
        mode.set("b")
        assert "B: 20" in switch.render()
    
    def test_switch_condition_with_store_array(self):
        """Switch with Store array condition."""
        store = Store({"items": []})
        switch = Switch()[
            Match(when=lambda: len(list(store.items)) > 5)["Many"],
            Match(when=lambda: len(list(store.items)) > 0)["Some"],
            Match(when=True)["Empty"]
        ]
        
        assert "Empty" in switch.render()
    
    def test_switch_boolean_signal(self):
        """Switch with boolean Signal."""
        is_active = Signal(True)
        switch = Switch()[
            Match(when=lambda: is_active())["Active"],
            Match(when=True)["Inactive"]
        ]
        
        assert "Active" in switch.render()
        
        is_active.set(False)
        assert "Inactive" in switch.render()
    
    def test_switch_string_comparison(self):
        """Switch with string comparison."""
        theme = Signal("dark")
        switch = Switch()[
            Match(when=lambda: theme() == "dark")["🌙 Dark"],
            Match(when=lambda: theme() == "light")["☀️ Light"],
            Match(when=True)["System"]
        ]
        
        assert "Dark" in switch.render()
        
        theme.set("light")
        assert "Light" in switch.render()
    
    def test_switch_none_handling(self):
        """Switch handles None in signal."""
        value = Signal(None)
        switch = Switch()[
            Match(when=lambda: value() is None)["No value"],
            Match(when=True)["Has value"]
        ]
        
        assert "No value" in switch.render()
        
        value.set("something")
        assert "Has value" in switch.render()
    
    def test_switch_rerender_consistency(self):
        """Switch renders consistently across multiple calls."""
        status = Signal("active")
        switch = Switch()[
            Match(when=lambda: status() == "active")["Active"],
            Match(when=True)["Other"]
        ]
        
        html1 = switch.render()
        html2 = switch.render()
        html3 = switch.render()
        
        assert html1 == html2 == html3


# =============================================================================
# SECTION 3: EDGE CASES (15 tests)
# =============================================================================

class TestSwitchEdgeCases:
    """Edge case tests for Switch/Match."""
    
    def test_switch_none_condition(self):
        """Switch handles None condition."""
        switch = Switch()[
            Match(when=None)["Null"],
            Match(when=True)["Default"]
        ]
        html = switch.render()
        
        assert "Default" in html
        assert "Null" not in html
    
    def test_switch_empty_content(self):
        """Switch handles empty content."""
        switch = Switch()[
            Match(when=True)[""]
        ]
        html = switch.render()
        
        assert 'data-switch=' in html
    
    def test_switch_none_content(self):
        """Switch handles None content."""
        switch = Switch()[
            Match(when=True)[None]
        ]
        html = switch.render()
        
        assert 'data-switch=' in html
    
    def test_switch_nested_switch(self):
        """Switch can contain nested Switch."""
        outer = Switch()[
            Match(when=True)[
                Switch()[
                    Match(when=True)["Inner"]
                ]
            ]
        ]
        html = outer.render()
        
        assert "Inner" in html
    
    def test_switch_exception_in_condition(self):
        """Switch handles exception in condition."""
        def bad_condition():
            raise ValueError("Bad!")
        
        switch = Switch()[
            Match(when=bad_condition)["Bad"]
        ]
        
        with pytest.raises(ValueError):
            switch.render()
    
    def test_switch_exception_in_content(self):
        """Switch handles exception in content."""
        switch = Switch()[
            Match(when=True)[lambda: 1/0]
        ]
        
        with pytest.raises(ZeroDivisionError):
            switch.render()
    
    def test_switch_html_in_content(self):
        """Switch renders HTML in content."""
        switch = Switch()[
            Match(when=True)["<strong>Bold</strong>"]
        ]
        html = switch.render()
        
        assert "<strong>Bold</strong>" in html
    
    def test_switch_unicode_content(self):
        """Switch handles unicode content."""
        switch = Switch()[
            Match(when=True)["Hello 世界 🎉"]
        ]
        html = switch.render()
        
        assert "世界" in html
        assert "🎉" in html
    
    def test_switch_list_content(self):
        """Switch handles list content."""
        switch = Switch()[
            Match(when=True)[["Part 1", " ", "Part 2"]]
        ]
        html = switch.render()
        
        assert "Part 1" in html
        assert "Part 2" in html
    
    def test_switch_many_matches(self):
        """Switch handles many matches."""
        matches = [Match(when=i == 5)[f"Match {i}"] for i in range(10)]
        switch = Switch()[matches]
        html = switch.render()
        
        assert "Match 5" in html
    
    def test_switch_all_false_conditions(self):
        """Switch with all false conditions."""
        switch = Switch()[
            Match(when=False)["A"],
            Match(when=False)["B"],
            Match(when=False)["C"]
        ]
        html = switch.render()
        
        assert "A" not in html
        assert "B" not in html
        assert "C" not in html
    
    def test_switch_match_order_matters(self):
        """Match order determines which renders."""
        switch = Switch()[
            Match(when=True)["First"],
            Match(when=True)["Second"]
        ]
        html = switch.render()
        
        # First match should win
        assert "First" in html
        assert "Second" not in html
    
    def test_match_without_children(self):
        """Match without children renders empty."""
        match = Match(when=True)
        html = match.render()
        
        assert html == ""
    
    def test_switch_single_match_in_list(self):
        """Switch with single Match in list."""
        switch = Switch()[[Match(when=True)["Single"]]]
        html = switch.render()
        
        assert "Single" in html
    
    def test_switch_callable_content(self):
        """Switch with callable content."""
        counter = [0]
        
        def get_content():
            counter[0] += 1
            return f"Called {counter[0]} times"
        
        switch = Switch()[
            Match(when=True)[get_content]
        ]
        
        html1 = switch.render()
        assert "Called 1 times" in html1
        
        html2 = switch.render()
        assert "Called 2 times" in html2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

