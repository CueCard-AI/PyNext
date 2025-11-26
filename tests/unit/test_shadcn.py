"""
Tests for PyNext ShadCN components
"""

import pytest


class TestTailwindBuilder:
    """Tests for the tw class builder"""
    
    def test_simple_classes(self):
        from pynext.tw import tw
        
        result = str(tw.flex.items_center.justify_between)
        assert "flex" in result
        assert "items-center" in result
        assert "justify-between" in result
    
    def test_classes_with_values(self):
        from pynext.tw import tw
        
        result = str(tw.p(4).m(2).bg("blue-500"))
        assert "p-4" in result
        assert "m-2" in result
        assert "bg-blue-500" in result
    
    def test_modifier_classes(self):
        from pynext.tw import tw
        
        result = str(tw.hover.bg("blue-600"))
        assert "hover:bg-blue-600" in result
    
    def test_responsive_modifiers(self):
        from pynext.tw import tw
        
        result = str(tw.md.flex.lg.hidden)
        assert "md:flex" in result
        assert "lg:hidden" in result
    
    def test_raw_string(self):
        from pynext.tw import tw
        
        result = str(tw("flex items-center p-4"))
        assert "flex" in result
        assert "items-center" in result
        assert "p-4" in result


class TestCn:
    """Tests for the cn utility"""
    
    def test_simple_merge(self):
        from pynext.tw import cn
        
        result = cn("foo", "bar")
        assert "foo" in result
        assert "bar" in result
    
    def test_conditional_classes(self):
        from pynext.tw import cn
        
        result = cn("base", True and "active", False and "inactive")
        assert "base" in result
        assert "active" in result
        assert "inactive" not in result
    
    def test_conflict_resolution(self):
        from pynext.tw import cn
        
        # Last occurrence should win
        result = cn("p-4", "p-2")
        assert "p-2" in result
        # p-4 should be removed
        assert result.count("p-") == 1
    
    def test_empty_and_none(self):
        from pynext.tw import cn
        
        result = cn("foo", None, "", False, "bar")
        assert result == "foo bar"


class TestButton:
    """Tests for the Button component"""
    
    def test_basic_button(self):
        from pynext.shadcn import Button
        
        html = Button()["Click me"].render()
        assert "<button" in html
        assert "Click me" in html
        assert 'type="button"' in html
    
    def test_button_variants(self):
        from pynext.shadcn import Button
        
        default = Button(variant="default")["Test"].render()
        assert "bg-primary" in default
        
        destructive = Button(variant="destructive")["Test"].render()
        assert "bg-destructive" in destructive
        
        outline = Button(variant="outline")["Test"].render()
        assert "border" in outline
    
    def test_button_sizes(self):
        from pynext.shadcn import Button
        
        sm = Button(size="sm")["Test"].render()
        assert "h-9" in sm
        
        lg = Button(size="lg")["Test"].render()
        assert "h-11" in lg
    
    def test_disabled_button(self):
        from pynext.shadcn import Button
        
        html = Button(disabled=True)["Test"].render()
        assert "disabled" in html


class TestInput:
    """Tests for Input, Label, Textarea"""
    
    def test_basic_input(self):
        from pynext.shadcn import Input
        
        html = Input(placeholder="Enter text").render()
        assert "<input" in html
        assert 'placeholder="Enter text"' in html
        assert 'type="text"' in html
    
    def test_input_types(self):
        from pynext.shadcn import Input
        
        email = Input(type="email").render()
        assert 'type="email"' in email
        
        password = Input(type="password").render()
        assert 'type="password"' in password
    
    def test_label(self):
        from pynext.shadcn import Label
        
        html = Label(html_for="email")["Email"].render()
        assert "<label" in html
        assert 'for="email"' in html
        assert "Email" in html
    
    def test_textarea(self):
        from pynext.shadcn import Textarea
        
        html = Textarea(placeholder="Enter bio", rows=5).render()
        assert "<textarea" in html
        assert 'placeholder="Enter bio"' in html
        assert 'rows="5"' in html


class TestCard:
    """Tests for Card components"""
    
    def test_basic_card(self):
        from pynext.shadcn import Card, CardHeader, CardTitle, CardContent
        
        html = Card()[
            CardHeader()[CardTitle()["Title"]],
            CardContent()["Content"]
        ].render()
        
        assert "rounded-lg" in html
        assert "Title" in html
        assert "Content" in html
    
    def test_card_sections(self):
        from pynext.shadcn import CardHeader, CardTitle, CardDescription
        
        header = CardHeader()[
            CardTitle()["Test Title"],
            CardDescription()["Test Description"]
        ].render()
        
        assert "<h3" in header  # CardTitle uses h3
        assert "Test Title" in header
        assert "Test Description" in header


class TestBadge:
    """Tests for Badge component"""
    
    def test_badge_variants(self):
        from pynext.shadcn import Badge
        
        default = Badge()["New"].render()
        assert "bg-primary" in default
        
        destructive = Badge(variant="destructive")["Error"].render()
        assert "bg-destructive" in destructive
        
        outline = Badge(variant="outline")["Preview"].render()
        assert "outline" in outline or "text-foreground" in outline


class TestAlert:
    """Tests for Alert component"""
    
    def test_basic_alert(self):
        from pynext.shadcn import Alert, AlertTitle, AlertDescription
        
        html = Alert()[
            AlertTitle()["Notice"],
            AlertDescription()["This is important"]
        ].render()
        
        assert 'role="alert"' in html
        assert "Notice" in html
        assert "This is important" in html
    
    def test_destructive_alert(self):
        from pynext.shadcn import Alert
        
        html = Alert(variant="destructive")["Error"].render()
        assert "destructive" in html


class TestDialog:
    """Tests for Dialog component"""
    
    def test_dialog_structure(self):
        from pynext.shadcn import Dialog, DialogTrigger, DialogContent, DialogTitle
        
        html = Dialog()[
            DialogTrigger()["Open"],
            DialogContent()[
                DialogTitle()["Title"]
            ]
        ].render()
        
        assert "data-pynext-dialog" in html
        assert "Title" in html


class TestTabs:
    """Tests for Tabs component"""
    
    def test_tabs_structure(self):
        from pynext.shadcn import Tabs, TabsList, TabsTrigger, TabsContent
        
        html = Tabs(default_value="tab1")[
            TabsList()[
                TabsTrigger(value="tab1")["Tab 1"],
                TabsTrigger(value="tab2")["Tab 2"]
            ],
            TabsContent(value="tab1")["Content 1"],
            TabsContent(value="tab2")["Content 2"]
        ].render()
        
        assert "data-pynext-tabs" in html
        assert 'role="tablist"' in html
        assert 'role="tabpanel"' in html


class TestAccordion:
    """Tests for Accordion component"""
    
    def test_accordion_structure(self):
        from pynext.shadcn import Accordion, AccordionItem, AccordionTrigger, AccordionContent
        
        html = Accordion(type="single")[
            AccordionItem(value="item-1")[
                AccordionTrigger()["Question"],
                AccordionContent()["Answer"]
            ]
        ].render()
        
        assert "data-pynext-accordion" in html
        assert "Question" in html
        assert "Answer" in html


class TestFormControls:
    """Tests for form control components"""
    
    def test_switch(self):
        from pynext.shadcn import Switch
        
        html = Switch(checked=True).render()
        assert 'role="switch"' in html
        assert 'data-state="checked"' in html
    
    def test_checkbox(self):
        from pynext.shadcn import Checkbox
        
        html = Checkbox(checked=True).render()
        assert 'role="checkbox"' in html
        assert 'data-state="checked"' in html
    
    def test_radio_group(self):
        from pynext.shadcn import RadioGroup, RadioGroupItem
        
        html = RadioGroup()[
            RadioGroupItem(value="a"),
            RadioGroupItem(value="b")
        ].render()
        
        assert 'role="radiogroup"' in html
        assert 'data-value="a"' in html
        assert 'data-value="b"' in html


class TestReactWrapper:
    """Tests for React component wrapper"""
    
    def test_use_react(self):
        from pynext.react import use_react
        
        DatePicker = use_react("react-datepicker")
        assert DatePicker.package == "react-datepicker"
        assert DatePicker.export_name is None
    
    def test_use_react_named_export(self):
        from pynext.react import use_react
        
        Carousel = use_react("embla-carousel-react", "Carousel")
        assert Carousel.package == "embla-carousel-react"
        assert Carousel.export_name == "Carousel"
    
    def test_react_island_render(self):
        from pynext.react import use_react
        
        DatePicker = use_react("react-datepicker")
        html = DatePicker(selected="2024-01-01").render()
        
        assert "data-pynext-react-island" in html
        assert 'data-package="react-datepicker"' in html
        assert "2024-01-01" in html

