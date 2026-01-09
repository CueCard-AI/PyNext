"""
Phase 34.3: CSS Typed OM Parity Tests

Mini-application tests verifying Python-to-JavaScript parity for CSS Typed OM.
These tests ensure complete applications using typed CSS values work correctly.

Total: 30 tests
"""

import pytest
from pynext.transpiler import transpile


# =============================================================================
# Theme System Mini-App Tests (6 tests)
# =============================================================================

class TestThemeSystem:
    """Integration tests for theme systems using CSS Typed OM."""
    
    def test_complete_theme_with_typed_values(self):
        """Complete theme setup with typed values should work."""
        code = '''
from pynext.client import document, CSS

# Define spacing scale using typed values
spacing_xs = CSS.rem(0.25)
spacing_sm = CSS.rem(0.5)
spacing_md = CSS.rem(1)
spacing_lg = CSS.rem(2)
spacing_xl = CSS.rem(4)

# Apply to container
container = document.getElementById("container")
style_map = container.attributeStyleMap

style_map.set("padding", spacing_lg)
style_map.set("margin", spacing_md)
'''
        result = transpile(code)
        assert 'CSS.rem' in result
        assert 'attributeStyleMap' in result
        assert 'set("padding"' in result
        assert "__py." not in result
    
    def test_responsive_font_sizes(self):
        """Responsive typography with clamp should work."""
        code = '''
from pynext.client import document, CSS

# Fluid typography
h1_size = CSS.clamp(CSS.rem(2), CSS.vw(5), CSS.rem(4))
body_size = CSS.clamp(CSS.rem(1), CSS.vw(1.5), CSS.rem(1.25))

heading = document.querySelector("h1")
heading.attributeStyleMap.set("font-size", h1_size)

body = document.body
body.attributeStyleMap.set("font-size", body_size)
'''
        result = transpile(code)
        assert 'CSS.clamp' in result
        assert 'CSS.rem' in result
        assert 'CSS.vw' in result
    
    def test_color_palette_with_manipulation(self):
        """Color palette with manipulation should work."""
        code = '''
from pynext.client import document, CSS

# Base color
primary = CSS.oklch(0.7, 0.15, 250)

# Derived colors
primary_light = primary.lighten(20)
primary_dark = primary.darken(20)
primary_muted = primary.desaturate(30)

# Apply colors
btn = document.getElementById("btn")
btn.attributeStyleMap.set("background-color", primary)
'''
        result = transpile(code)
        assert 'CSS.oklch' in result
        assert 'lighten' in result
        assert 'darken' in result
    
    def test_dynamic_spacing_calculation(self):
        """Dynamic spacing with arithmetic should work."""
        code = '''
from pynext.client import document, CSS

# Base spacing
base = CSS.rem(1)

# Calculate derived values
half = base.div(2)
double = base.mul(2)
triple = base.mul(3)

# Grid gap
grid = document.getElementById("grid")
style_map = grid.attributeStyleMap
style_map.set("gap", double)
style_map.set("padding", triple)
'''
        result = transpile(code)
        assert 'div(2)' in result
        assert 'mul(2)' in result
        assert 'mul(3)' in result
    
    def test_theme_switch_with_typed_values(self):
        """Theme switching with typed values should work."""
        code = '''
from pynext.client import document, CSS

def apply_theme(dark_mode):
    root = document.documentElement.attributeStyleMap
    
    if dark_mode:
        root.set("--bg", CSS.rgb(15, 23, 42))
        root.set("--fg", CSS.rgb(241, 245, 249))
    else:
        root.set("--bg", CSS.rgb(255, 255, 255))
        root.set("--fg", CSS.rgb(26, 26, 26))

apply_theme(True)
'''
        result = transpile(code)
        assert 'CSS.rgb' in result
        assert 'attributeStyleMap' in result
    
    def test_semantic_tokens(self):
        """Semantic design tokens with typed values should work."""
        code = '''
from pynext.client import document, CSS

# Semantic size tokens
button_padding_x = CSS.rem(1)
button_padding_y = CSS.rem(0.5)
button_radius = CSS.px(8)

# Apply to button
btn = document.getElementById("submit-btn")
style_map = btn.attributeStyleMap
style_map.set("padding-left", button_padding_x)
style_map.set("padding-right", button_padding_x)
style_map.set("padding-top", button_padding_y)
style_map.set("padding-bottom", button_padding_y)
style_map.set("border-radius", button_radius)
'''
        result = transpile(code)
        assert 'CSS.rem' in result
        assert 'CSS.px' in result


# =============================================================================
# Layout Mini-App Tests (6 tests)
# =============================================================================

class TestLayoutApps:
    """Integration tests for layout systems using CSS Typed OM."""
    
    def test_responsive_grid_layout(self):
        """Responsive grid with viewport units should work."""
        code = '''
from pynext.client import document, CSS

grid = document.getElementById("main-grid")
style_map = grid.attributeStyleMap

# Responsive columns
col_width = CSS.min(CSS.px(300), CSS.vw(100))
style_map.set("grid-template-columns", col_width)
style_map.set("gap", CSS.rem(1))
style_map.set("padding", CSS.vw(2))
'''
        result = transpile(code)
        assert 'CSS.min' in result
        assert 'CSS.vw' in result
    
    def test_centered_container(self):
        """Centered container with max-width should work."""
        code = '''
from pynext.client import document, CSS

container = document.getElementById("container")
style_map = container.attributeStyleMap

style_map.set("width", CSS.percent(100))
style_map.set("max-width", CSS.px(1200))
style_map.set("margin-left", CSS.keyword("auto"))
style_map.set("margin-right", CSS.keyword("auto"))
style_map.set("padding-left", CSS.rem(1))
style_map.set("padding-right", CSS.rem(1))
'''
        result = transpile(code)
        assert 'CSS.percent' in result
        assert 'CSS.keyword("auto")' in result
    
    def test_flex_layout_with_gaps(self):
        """Flexbox layout with typed gaps should work."""
        code = '''
from pynext.client import document, CSS

nav = document.getElementById("nav")
style_map = nav.attributeStyleMap

style_map.set("display", CSS.keyword("flex"))
style_map.set("gap", CSS.rem(1.5))
style_map.set("align-items", CSS.keyword("center"))
style_map.set("padding", CSS.rem(1))
'''
        result = transpile(code)
        assert 'CSS.keyword("flex")' in result
    
    def test_aspect_ratio_box(self):
        """Aspect ratio box with calc should work."""
        code = '''
from pynext.client import document, CSS

video_container = document.getElementById("video")
style_map = video_container.attributeStyleMap

style_map.set("width", CSS.percent(100))
style_map.set("padding-bottom", CSS.calc("100% / (16 / 9)"))
style_map.set("position", CSS.keyword("relative"))
'''
        result = transpile(code)
        assert 'CSS.calc' in result
    
    def test_sticky_header(self):
        """Sticky header with position values should work."""
        code = '''
from pynext.client import document, CSS

header = document.getElementById("header")
style_map = header.attributeStyleMap

style_map.set("position", CSS.keyword("sticky"))
style_map.set("top", CSS.px(0))
style_map.set("z-index", CSS.number(100))
style_map.set("height", CSS.px(64))
'''
        result = transpile(code)
        assert 'CSS.keyword("sticky")' in result
        assert 'CSS.number' in result
    
    def test_sidebar_layout(self):
        """Sidebar layout with fr units should work."""
        code = '''
from pynext.client import document, CSS

layout = document.getElementById("layout")
style_map = layout.attributeStyleMap

style_map.set("display", CSS.keyword("grid"))
# Sidebar: 250px, main: rest of space
sidebar_width = CSS.px(250)
'''
        result = transpile(code)
        assert 'CSS.keyword("grid")' in result


# =============================================================================
# Animation Mini-App Tests (6 tests)
# =============================================================================

class TestAnimationApps:
    """Integration tests for animations using CSS Typed OM."""
    
    def test_transform_animation_keyframes(self):
        """Animation with typed transforms should work."""
        code = '''
from pynext.client import document, CSS, CSSTransformValue

def animate_card(card):
    style_map = card.attributeStyleMap
    
    # Set initial transform
    initial = CSSTransformValue([
        CSS.translate(CSS.px(0), CSS.px(0)),
        CSS.scale(1),
    ])
    style_map.set("transform", initial)
'''
        result = transpile(code)
        assert 'CSSTransformValue' in result
        assert 'CSS.translate' in result
        assert 'CSS.scale' in result
    
    def test_rotation_animation(self):
        """Rotation animation with typed angles should work."""
        code = '''
from pynext.client import document, CSS, CSSTransformValue

spinner = document.getElementById("spinner")
style_map = spinner.attributeStyleMap

# Rotating transform
rotation = CSS.rotate(CSS.deg(0))
style_map.set("transform", CSSTransformValue([rotation]))

def update_rotation(degrees):
    new_rotation = CSS.rotate(CSS.deg(degrees))
    style_map.set("transform", CSSTransformValue([new_rotation]))
'''
        result = transpile(code)
        assert 'CSS.rotate' in result
        assert 'CSS.deg' in result
    
    def test_slide_animation(self):
        """Slide animation with translate should work."""
        code = '''
from pynext.client import document, CSS, CSSTransformValue

panel = document.getElementById("slide-panel")

def slide_in():
    style_map = panel.attributeStyleMap
    transform = CSSTransformValue([
        CSS.translateX(CSS.percent(0)),
    ])
    style_map.set("transform", transform)

def slide_out():
    style_map = panel.attributeStyleMap
    transform = CSSTransformValue([
        CSS.translateX(CSS.percent(-100)),
    ])
    style_map.set("transform", transform)
'''
        result = transpile(code)
        assert 'CSS.translateX' in result
        assert 'CSS.percent' in result
    
    def test_3d_transform(self):
        """3D transforms with perspective should work."""
        code = '''
from pynext.client import document, CSS, CSSTransformValue

card = document.getElementById("flip-card")
style_map = card.attributeStyleMap

# Set perspective
style_map.set("perspective", CSS.px(1000))

# 3D rotation
front_transform = CSSTransformValue([
    CSS.rotateY(CSS.deg(0)),
])
style_map.set("transform", front_transform)
'''
        result = transpile(code)
        assert 'CSS.rotateY' in result
        assert 'perspective' in result
    
    def test_scale_on_hover(self):
        """Scale transform for hover effect should work."""
        code = '''
from pynext.client import document, CSS, CSSTransformValue

button = document.getElementById("hover-btn")

def on_mouse_enter(e):
    transform = CSSTransformValue([CSS.scale(1.05)])
    e.target.attributeStyleMap.set("transform", transform)

def on_mouse_leave(e):
    transform = CSSTransformValue([CSS.scale(1)])
    e.target.attributeStyleMap.set("transform", transform)

button.addEventListener("mouseenter", on_mouse_enter)
button.addEventListener("mouseleave", on_mouse_leave)
'''
        result = transpile(code)
        assert 'CSS.scale' in result
        assert 'addEventListener' in result
    
    def test_complex_transform_sequence(self):
        """Complex transform combining multiple operations should work."""
        code = '''
from pynext.client import document, CSS, CSSTransformValue

element = document.getElementById("animated")
style_map = element.attributeStyleMap

# Complex transform: translate + rotate + scale
transform = CSSTransformValue([
    CSS.translate(CSS.px(100), CSS.px(50)),
    CSS.rotate(CSS.deg(45)),
    CSS.scale(1.5),
])
style_map.set("transform", transform)
'''
        result = transpile(code)
        assert 'CSS.translate' in result
        assert 'CSS.rotate' in result
        assert 'CSS.scale' in result


# =============================================================================
# Component Mini-App Tests (6 tests)
# =============================================================================

class TestComponentApps:
    """Integration tests for UI components using CSS Typed OM."""
    
    def test_button_component_styling(self):
        """Button component with typed styles should work."""
        code = '''
from pynext.client import document, CSS

def style_button(btn, variant):
    style_map = btn.attributeStyleMap
    
    style_map.set("padding-left", CSS.rem(1))
    style_map.set("padding-right", CSS.rem(1))
    style_map.set("padding-top", CSS.rem(0.5))
    style_map.set("padding-bottom", CSS.rem(0.5))
    style_map.set("border-radius", CSS.px(4))
    
    if variant == "primary":
        style_map.set("background-color", CSS.rgb(59, 130, 246))
    elif variant == "secondary":
        style_map.set("background-color", CSS.rgb(100, 116, 139))

btn = document.getElementById("submit")
style_button(btn, "primary")
'''
        result = transpile(code)
        assert 'CSS.rem' in result
        assert 'CSS.rgb' in result
    
    def test_modal_positioning(self):
        """Modal with centered positioning should work."""
        code = '''
from pynext.client import document, CSS

modal = document.getElementById("modal")
style_map = modal.attributeStyleMap

style_map.set("position", CSS.keyword("fixed"))
style_map.set("top", CSS.percent(50))
style_map.set("left", CSS.percent(50))
style_map.set("transform", CSSTransformValue([
    CSS.translate(CSS.percent(-50), CSS.percent(-50)),
]))
style_map.set("max-width", CSS.px(500))
style_map.set("width", CSS.percent(90))
'''
        result = transpile(code)
        assert 'CSS.keyword("fixed")' in result
        assert 'CSS.percent' in result
    
    def test_tooltip_positioning(self):
        """Tooltip positioning with offset should work."""
        code = '''
from pynext.client import document, CSS

def show_tooltip(target, tooltip):
    # Get target position
    rect = target.getBoundingClientRect()
    
    style_map = tooltip.attributeStyleMap
    style_map.set("position", CSS.keyword("absolute"))
    style_map.set("top", CSS.px(rect.bottom + 8))
    style_map.set("left", CSS.px(rect.left))
'''
        result = transpile(code)
        assert 'CSS.keyword("absolute")' in result
        assert 'CSS.px' in result
    
    def test_progress_bar(self):
        """Progress bar with percentage width should work."""
        code = '''
from pynext.client import document, CSS

def update_progress(progress_el, percent):
    style_map = progress_el.attributeStyleMap
    style_map.set("width", CSS.percent(percent))

progress = document.getElementById("progress-bar")
update_progress(progress, 75)
'''
        result = transpile(code)
        assert 'CSS.percent' in result
    
    def test_card_shadow_and_radius(self):
        """Card with shadow and radius using typed values should work."""
        code = '''
from pynext.client import document, CSS

card = document.getElementById("card")
style_map = card.attributeStyleMap

style_map.set("border-radius", CSS.px(8))
style_map.set("padding", CSS.rem(1.5))
style_map.set("margin", CSS.rem(1))
'''
        result = transpile(code)
        assert 'CSS.px' in result
        assert 'CSS.rem' in result
    
    def test_avatar_sizing(self):
        """Avatar component with consistent sizing should work."""
        code = '''
from pynext.client import document, CSS

def style_avatar(avatar, size):
    style_map = avatar.attributeStyleMap
    
    sizes = {
        "sm": CSS.px(32),
        "md": CSS.px(48),
        "lg": CSS.px(64),
    }
    
    dimension = sizes.get(size, sizes["md"])
    style_map.set("width", dimension)
    style_map.set("height", dimension)
    style_map.set("border-radius", CSS.percent(50))

avatar = document.getElementById("user-avatar")
style_avatar(avatar, "lg")
'''
        result = transpile(code)
        assert 'CSS.px' in result
        assert 'CSS.percent(50)' in result


# =============================================================================
# Computed Style Reading Tests (6 tests)
# =============================================================================

class TestComputedStyleReading:
    """Integration tests for reading computed styles."""
    
    def test_read_and_double_width(self):
        """Reading width and doubling it should work."""
        code = '''
from pynext.client import document, CSS

el = document.getElementById("box")
computed = el.computedStyleMap()
width = computed.get("width")

if width:
    doubled = width.mul(2)
    el.attributeStyleMap.set("width", doubled)
'''
        result = transpile(code)
        assert 'computedStyleMap()' in result
        assert 'mul(2)' in result
    
    def test_read_and_apply_to_sibling(self):
        """Copying computed style to sibling should work."""
        code = '''
from pynext.client import document

source = document.getElementById("source")
target = document.getElementById("target")

source_height = source.computedStyleMap().get("height")
if source_height:
    target.attributeStyleMap.set("height", source_height)
'''
        result = transpile(code)
        assert 'computedStyleMap()' in result
        assert 'attributeStyleMap' in result
    
    def test_conditional_style_based_on_computed(self):
        """Conditional styling based on computed value should work."""
        code = '''
from pynext.client import document, CSS

el = document.getElementById("box")
computed = el.computedStyleMap()
width = computed.get("width")

if width and width.value > 500:
    el.attributeStyleMap.set("flex-direction", CSS.keyword("row"))
else:
    el.attributeStyleMap.set("flex-direction", CSS.keyword("column"))
'''
        result = transpile(code)
        assert 'width.value' in result
        assert 'CSS.keyword' in result
    
    def test_extract_all_dimensions(self):
        """Extracting all dimensions from computed styles should work."""
        code = '''
from pynext.client import document

el = document.getElementById("box")
computed = el.computedStyleMap()

width = computed.get("width")
height = computed.get("height")
padding_top = computed.get("padding-top")
margin_left = computed.get("margin-left")
'''
        result = transpile(code)
        # All four dimensions should be accessed
        assert '"width"' in result
        assert '"height"' in result
        assert '"padding-top"' in result
        assert '"margin-left"' in result
    
    def test_iterate_all_styles(self):
        """Iterating all computed styles should work."""
        code = '''
from pynext.client import document

el = document.getElementById("box")
computed = el.computedStyleMap()

for prop in computed.keys():
    value = computed.get(prop)
    console.log(prop, value)
'''
        result = transpile(code)
        # Can use .keys() or Object.keys() - both work
        assert 'computed' in result
        assert 'console.log' in result
    
    def test_compare_computed_values(self):
        """Comparing computed values should work."""
        code = '''
from pynext.client import document

el1 = document.getElementById("box1")
el2 = document.getElementById("box2")

width1 = el1.computedStyleMap().get("width")
width2 = el2.computedStyleMap().get("width")

if width1 and width2:
    same = width1.equals(width2)
'''
        result = transpile(code)
        assert 'equals(' in result
