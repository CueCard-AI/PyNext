"""
PyNext Client - CSS Color Types

=============================================================================
WHAT THIS FILE DOES
=============================================================================

Provides Python type stubs for CSS Color types, enabling type-safe color
manipulation with IDE autocompletion. Includes color spaces (RGB, HSL, 
OKLCH, etc.) and manipulation methods (lighten, darken, mix, etc.).

=============================================================================
WHY THIS EXISTS
=============================================================================

Traditional CSS color handling uses strings:
    el.style.backgroundColor = "rgb(255, 0, 0)"  # No manipulation possible

CSS Typed OM + Color API provides typed colors:
    color = CSS.rgb(255, 0, 0)
    lighter = color.lighten(20)  # Programmatic manipulation!

Benefits:
- Type-safe color creation and manipulation
- IDE autocompletion for color methods
- Color space conversions
- Programmatic color adjustments

=============================================================================
HOW IT WORKS
=============================================================================

All color methods are **passthrough** - they transpile 1:1 to JavaScript.
Note: CSS Color API is still experimental in browsers. For wider support,
use string-based colors or polyfills.

=============================================================================
WHO USES THIS
=============================================================================

- Developers creating dynamic color themes
- Applications with color manipulation (lighten/darken)
- Design systems with computed color variants

=============================================================================
BROWSER SUPPORT
=============================================================================

CSS Color Level 4/5 features have varying browser support:
- Basic rgb(), hsl(): Universal
- oklch(), oklab(): Chrome 111+, Safari 15.4+
- Color manipulation (lighten, mix): Experimental/Polyfill needed

=============================================================================
EXAMPLES
=============================================================================

    from pynext.client import CSS
    from pynext.client.css_color import CSSColor
    
    # Create colors
    red = CSS.rgb(255, 0, 0)
    blue = CSS.hsl(240, 100, 50)
    
    # Manipulation (where supported)
    lighter_red = red.lighten(20)
    darker_blue = blue.darken(20)
    
    # Mix colors
    purple = red.mix(blue, 0.5)
    
    # Adjust alpha
    semi_transparent = red.alpha(0.5)
"""

from __future__ import annotations
from typing import Optional, Union


# =============================================================================
# CSS Color Value
# =============================================================================

class CSSColor:
    """
    WHO: Developers working with typed CSS colors
    WHAT: A typed CSS color value with manipulation methods
    WHEN: Use for dynamic color systems and computed colors
    WHERE: Client-side code (transpiles to browser APIs)
    WHY: Type-safe color handling with IDE support
    HOW: Zero-runtime passthrough where browser supports
    
    Note: Many color manipulation methods are experimental.
    For production, consider string-based colors or polyfills.
    
    Example:
        color = CSS.rgb(255, 128, 0)
        print(color.red, color.green, color.blue)
        
        lighter = color.lighten(20)
        with_alpha = color.alpha(0.5)
    """
    
    # =========================================================================
    # RGB Components
    # =========================================================================
    
    @property
    def red(self) -> float:
        """Red component (0-255 or 0-1 depending on creation)."""
        ...
    
    @property
    def green(self) -> float:
        """Green component."""
        ...
    
    @property
    def blue(self) -> float:
        """Blue component."""
        ...
    
    @property
    def alpha(self) -> float:
        """Alpha/opacity component (0-1)."""
        ...
    
    # =========================================================================
    # HSL Components
    # =========================================================================
    
    @property
    def hue(self) -> float:
        """Hue in degrees (0-360)."""
        ...
    
    @property
    def saturation(self) -> float:
        """Saturation percentage (0-100)."""
        ...
    
    @property
    def lightness(self) -> float:
        """Lightness percentage (0-100)."""
        ...
    
    # =========================================================================
    # OKLCH Components (perceptually uniform)
    # =========================================================================
    
    @property
    def l(self) -> float:
        """OKLCH lightness (0-1)."""
        ...
    
    @property
    def c(self) -> float:
        """OKLCH chroma."""
        ...
    
    @property
    def h(self) -> float:
        """OKLCH hue in degrees."""
        ...
    
    # =========================================================================
    # Conversion Methods
    # =========================================================================
    
    def toRGB(self) -> CSSColor:
        """Convert to RGB color space."""
        ...
    
    def toHSL(self) -> CSSColor:
        """Convert to HSL color space."""
        ...
    
    def toHWB(self) -> CSSColor:
        """Convert to HWB color space."""
        ...
    
    def toOKLCH(self) -> CSSColor:
        """Convert to OKLCH color space."""
        ...
    
    def toOKLAB(self) -> CSSColor:
        """Convert to OKLAB color space."""
        ...
    
    def toString(self) -> str:
        """Convert to CSS string representation."""
        ...
    
    def __str__(self) -> str:
        """Python string conversion."""
        ...
    
    # =========================================================================
    # Manipulation Methods
    # =========================================================================
    
    def lighten(self, amount: float) -> CSSColor:
        """
        Create a lighter version of this color.
        
        Args:
            amount: Amount to lighten (0-100 as percentage)
        
        Returns:
            New CSSColor that is lighter
        
        Example:
            lighter = color.lighten(20)  # 20% lighter
        """
        ...
    
    def darken(self, amount: float) -> CSSColor:
        """
        Create a darker version of this color.
        
        Args:
            amount: Amount to darken (0-100 as percentage)
        
        Returns:
            New CSSColor that is darker
        
        Example:
            darker = color.darken(20)  # 20% darker
        """
        ...
    
    def saturate(self, amount: float) -> CSSColor:
        """
        Increase saturation.
        
        Args:
            amount: Amount to increase (0-100 as percentage)
        
        Returns:
            New CSSColor with increased saturation
        """
        ...
    
    def desaturate(self, amount: float) -> CSSColor:
        """
        Decrease saturation.
        
        Args:
            amount: Amount to decrease (0-100 as percentage)
        
        Returns:
            New CSSColor with decreased saturation
        """
        ...
    
    def rotate(self, angle: float) -> CSSColor:
        """
        Rotate the hue.
        
        Args:
            angle: Degrees to rotate the hue
        
        Returns:
            New CSSColor with rotated hue
        
        Example:
            complementary = color.rotate(180)  # Complementary color
        """
        ...
    
    def invert(self) -> CSSColor:
        """
        Invert the color.
        
        Returns:
            New CSSColor that is the inverse
        """
        ...
    
    def grayscale(self) -> CSSColor:
        """
        Convert to grayscale.
        
        Returns:
            New grayscale CSSColor
        """
        ...
    
    def sepia(self) -> CSSColor:
        """
        Apply sepia tone.
        
        Returns:
            New CSSColor with sepia effect
        """
        ...
    
    def setAlpha(self, value: float) -> CSSColor:
        """
        Set the alpha/opacity.
        
        Args:
            value: New alpha value (0-1)
        
        Returns:
            New CSSColor with specified alpha
        
        Example:
            semi = color.setAlpha(0.5)  # 50% opacity
        """
        ...
    
    def fadeIn(self, amount: float) -> CSSColor:
        """
        Increase opacity.
        
        Args:
            amount: Amount to increase (0-1)
        
        Returns:
            New CSSColor with increased opacity
        """
        ...
    
    def fadeOut(self, amount: float) -> CSSColor:
        """
        Decrease opacity.
        
        Args:
            amount: Amount to decrease (0-1)
        
        Returns:
            New CSSColor with decreased opacity
        """
        ...
    
    def mix(self, other: CSSColor, weight: float = 0.5) -> CSSColor:
        """
        Mix with another color.
        
        Args:
            other: Color to mix with
            weight: Weight of the other color (0-1, default 0.5)
        
        Returns:
            New CSSColor that is a blend
        
        Example:
            purple = red.mix(blue)  # 50% mix
            mostly_red = red.mix(blue, 0.25)  # 75% red, 25% blue
        """
        ...
    
    def contrast(self, light: CSSColor, dark: CSSColor) -> CSSColor:
        """
        Choose a contrasting color based on this color's luminance.
        
        Args:
            light: Color to use if this is dark
            dark: Color to use if this is light
        
        Returns:
            The contrasting color
        
        Example:
            # Choose white or black text based on background
            text_color = bg_color.contrast(
                CSS.rgb(255, 255, 255),  # white for dark bg
                CSS.rgb(0, 0, 0),        # black for light bg
            )
        """
        ...
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def luminance(self) -> float:
        """
        Get the relative luminance.
        
        Returns:
            Luminance value (0-1)
        """
        ...
    
    def isLight(self) -> bool:
        """
        Check if this is a light color.
        
        Returns:
            True if luminance > 0.5
        """
        ...
    
    def isDark(self) -> bool:
        """
        Check if this is a dark color.
        
        Returns:
            True if luminance <= 0.5
        """
        ...
    
    def equals(self, other: CSSColor) -> bool:
        """
        Check equality with another color.
        
        Args:
            other: Color to compare
        
        Returns:
            True if colors are equal
        """
        ...


# =============================================================================
# CSS Color Factory Methods (extend CSS class)
# =============================================================================

class CSSColorFactory:
    """
    Color factory methods to be used via CSS namespace.
    
    These are actually static methods on the CSS class, documented here
    for clarity. Use as:
        CSS.rgb(255, 0, 0)
        CSS.hsl(0, 100, 50)
    """
    
    @staticmethod
    def color(name: str) -> CSSColor:
        """
        Create a color from a named color.
        
        Args:
            name: CSS color name ("red", "blue", "rebeccapurple", etc.)
        
        Returns:
            CSSColor for the named color
        
        Example:
            red = CSS.color("red")
            coral = CSS.color("coral")
        """
        ...
    
    @staticmethod
    def rgb(
        r: Union[int, float],
        g: Union[int, float],
        b: Union[int, float],
        a: float = 1.0
    ) -> CSSColor:
        """
        Create an RGB color.
        
        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            a: Alpha component (0-1, default 1.0)
        
        Returns:
            CSSColor in RGB space
        
        Example:
            red = CSS.rgb(255, 0, 0)
            semi_red = CSS.rgb(255, 0, 0, 0.5)
        """
        ...
    
    @staticmethod
    def rgba(r: int, g: int, b: int, a: float) -> CSSColor:
        """
        Create an RGBA color (alias for rgb with alpha).
        
        Args:
            r, g, b: Color components (0-255)
            a: Alpha (0-1)
        
        Returns:
            CSSColor with specified alpha
        """
        ...
    
    @staticmethod
    def hsl(h: float, s: float, l: float, a: float = 1.0) -> CSSColor:
        """
        Create an HSL color.
        
        Args:
            h: Hue in degrees (0-360)
            s: Saturation percentage (0-100)
            l: Lightness percentage (0-100)
            a: Alpha (0-1, default 1.0)
        
        Returns:
            CSSColor in HSL space
        
        Example:
            red = CSS.hsl(0, 100, 50)
            blue = CSS.hsl(240, 100, 50)
        """
        ...
    
    @staticmethod
    def hsla(h: float, s: float, l: float, a: float) -> CSSColor:
        """Create an HSLA color (alias for hsl with alpha)."""
        ...
    
    @staticmethod
    def hwb(h: float, w: float, b: float, a: float = 1.0) -> CSSColor:
        """
        Create an HWB color.
        
        Args:
            h: Hue in degrees (0-360)
            w: Whiteness percentage (0-100)
            b: Blackness percentage (0-100)
            a: Alpha (0-1, default 1.0)
        
        Returns:
            CSSColor in HWB space
        """
        ...
    
    @staticmethod
    def oklch(l: float, c: float, h: float, a: float = 1.0) -> CSSColor:
        """
        Create an OKLCH color (perceptually uniform).
        
        OKLCH is excellent for creating color palettes with consistent
        perceived lightness and saturation.
        
        Args:
            l: Lightness (0-1)
            c: Chroma (0-~0.4)
            h: Hue in degrees (0-360)
            a: Alpha (0-1, default 1.0)
        
        Returns:
            CSSColor in OKLCH space
        
        Example:
            blue = CSS.oklch(0.7, 0.15, 250)
        """
        ...
    
    @staticmethod
    def oklab(l: float, a_axis: float, b_axis: float, alpha: float = 1.0) -> CSSColor:
        """
        Create an OKLAB color.
        
        Args:
            l: Lightness (0-1)
            a_axis: Green-red axis
            b_axis: Blue-yellow axis
            alpha: Alpha (0-1, default 1.0)
        
        Returns:
            CSSColor in OKLAB space
        """
        ...
    
    @staticmethod
    def lab(l: float, a_axis: float, b_axis: float, alpha: float = 1.0) -> CSSColor:
        """
        Create a LAB color.
        
        Args:
            l: Lightness (0-100)
            a_axis: Green-red axis
            b_axis: Blue-yellow axis
            alpha: Alpha (0-1, default 1.0)
        
        Returns:
            CSSColor in LAB space
        """
        ...
    
    @staticmethod
    def lch(l: float, c: float, h: float, a: float = 1.0) -> CSSColor:
        """
        Create an LCH color.
        
        Args:
            l: Lightness (0-100)
            c: Chroma
            h: Hue in degrees (0-360)
            a: Alpha (0-1, default 1.0)
        
        Returns:
            CSSColor in LCH space
        """
        ...
    
    @staticmethod
    def hex(value: str) -> CSSColor:
        """
        Create a color from hex string.
        
        Args:
            value: Hex color string (#RGB, #RRGGBB, #RRGGBBAA)
        
        Returns:
            CSSColor
        
        Example:
            red = CSS.hex("#ff0000")
            blue = CSS.hex("#00f")  # Short form
        """
        ...


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "CSSColor",
    "CSSColorFactory",
]
